import logging
from typing import Any

from fastapi import APIRouter, Body, Depends
from planning_drawing_validator.types import RunID
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.api.constants import RunStatus
from backend.api.db_utils import get_or_404, validate_pagination
from backend.api.dependencies import get_db_session
from backend.api.models.requests import BulkDeleteRequest, RunUpdateRequest
from backend.api.models.responses import (
    ModelStatistics,
    ModelStatsResponse,
    RunDeleteResponse,
    RunDetailResponse,
    RunEventsResponse,
    RunListResponse,
    RunsClearResponse,
    RunSummary,
    RunUpdateResponse,
)
from backend.config import PaginationConfig
from backend.database.models import DocumentResult, Run as DBRun

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/runs", tags=["runs"])


def reconstruct_document_stages(events: list[dict[str, Any]], documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reconstruct document stages from run events.

    Analyses event history to build complete stage information for each document,
    including prompts, outputs, reasoning, and execution times.

    Args:
        events: List of run events with type, timestamp, and data.
        documents: List of document records to enrich with stage data.

    Returns:
        List of documents with reconstructed stage information.
    """
    # Build a map of document_id -> stages data from events
    doc_stages_map: dict[str, dict[str, Any]] = {}

    for event in events:
        event_type = event.get("type") or event.get("event_type")
        data = event.get("data", {})
        doc_id = data.get("document_id")

        if not doc_id:
            continue

        if doc_id not in doc_stages_map:
            doc_stages_map[doc_id] = {
                "stages": [
                    {"stage": 1, "stage_name": "Classification", "status": "pending"},
                    {"stage": 2, "stage_name": "Validation", "status": "pending"},
                ]
            }

        if event_type == "stage_started":
            stage_id = data.get("stage")
            if stage_id:
                # Handle both numeric and string stage identifiers
                for s in doc_stages_map[doc_id]["stages"]:
                    if s["stage"] in (
                        stage_id,
                        1 if stage_id == "classification" else 2 if stage_id == "validation" else None,
                    ):
                        s["status"] = "running"
                        s["prompt"] = data.get("prompt")

        elif event_type == "stage_completed":
            stage_id = data.get("stage")
            if stage_id:
                # Handle both numeric and string stage identifiers
                for s in doc_stages_map[doc_id]["stages"]:
                    if s["stage"] in (
                        stage_id,
                        1 if stage_id == "classification" else 2 if stage_id == "validation" else None,
                    ):
                        s["status"] = "completed"
                        s["prompt"] = data.get("prompt", s.get("prompt"))
                        s["model_output"] = data.get("model_output")
                        s["reasoning"] = data.get("reasoning")
                        s["confidence"] = data.get("confidence")
                        s["json_data"] = data.get("json_data", {})
                        s["execution_time"] = data.get("execution_time")

    # Merge documents with stage data
    documents_with_stages = []
    for doc in documents:
        document_id: str = doc.get("document_id", "")  # Default to empty string
        doc_with_stages = {
            **doc,
            "stages": doc_stages_map.get(document_id, {}).get(
                "stages",
                [
                    {"stage": 1, "stage_name": "Classification", "status": "completed"},
                    {"stage": 2, "stage_name": "Validation", "status": "completed"},
                ],
            ),
        }
        documents_with_stages.append(doc_with_stages)

    return documents_with_stages


def db_run_to_evaluation_run(db_run: DBRun, include_details: bool = False) -> dict[str, Any]:
    """Convert database Run model to evaluation run dictionary.

    Transforms a database Run object into a dictionary representation suitable
    for API responses. Optionally includes detailed document and event data.

    Args:
        db_run: Database Run model instance to convert.
        include_details: Whether to include full document and event details.

    Returns:
        Dictionary containing run metadata, document summaries, and event data.
    """
    documents = []
    events = []

    # Count errors from documents
    error_count = sum(1 for doc in db_run.documents if doc.predicted_validity == "ERROR")
    processed_count = db_run.completed_documents - error_count

    # Recalculate accuracy excluding errors
    if db_run.has_ground_truth and processed_count > 0:
        correct_count = sum(1 for doc in db_run.documents if doc.is_correct is True)
        accuracy = correct_count / processed_count
    else:
        accuracy = db_run.overall_accuracy or 0.0

    if include_details:
        # Load full document and event details
        for doc in db_run.documents:
            documents.append(
                {
                    "document_id": doc.document_id,
                    "filename": doc.filename,
                    "predicted_validity": doc.predicted_validity,
                    "predicted_reasoning": doc.predicted_reasoning,
                    "expected_validity": doc.expected_validity,
                    "is_correct": doc.is_correct,
                    "confidence": doc.confidence,
                    "prompt_type": doc.prompt_type,
                    "execution_time": doc.execution_time,
                    "stages": doc.stages,
                    # Reasoning evaluation fields
                    "reasoning_match_score": doc.reasoning_match_score,
                    "reasoning_evaluated": doc.reasoning_evaluated,
                    "reasoning_explanation": doc.reasoning_explanation,
                    "expected_reasoning": doc.expected_reasoning,
                }
            )

        for event in db_run.events:
            events.append(
                {
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data,
                }
            )

    return {
        "run_id": db_run.run_id,
        "timestamp": db_run.timestamp,
        "total_documents": db_run.total_documents,
        "completed_documents": db_run.completed_documents,
        "error_count": error_count,
        "processed_count": processed_count,
        "overall_accuracy": accuracy,
        "execution_time": db_run.execution_time,
        "status": db_run.status,
        "documents": documents,
        "events": events,
        "name": db_run.name,
        "has_ground_truth": db_run.has_ground_truth,
        "model_name": db_run.model_name,
        "reasoning_effort": db_run.reasoning_effort,
    }


@router.get("")
async def get_evaluation_runs(
    skip: int = 0,
    limit: int = PaginationConfig.DEFAULT_LIMIT,
    session: Session = Depends(get_db_session),
) -> RunListResponse:
    """Retrieve historical evaluation runs with pagination.

    Queries the database for evaluation runs, ordered by timestamp in
    descending order. Returns summarised run data without full document details.
    Supports pagination to handle large result sets efficiently.

    Args:
        skip: Number of runs to skip (for pagination). Default: 0.
        limit: Maximum number of runs to return. Default: 100, Max: 1000.
        session: Database session dependency for querying runs.

    Returns:
        RunListResponse containing list of run summaries with metadata and metrics.

    Raises:
        HTTPException: When limit exceeds maximum allowed value (400).
    """
    try:
        # Validate pagination parameters
        skip, limit = validate_pagination(skip, limit)

        db_runs = session.query(DBRun).order_by(DBRun.timestamp.desc()).offset(skip).limit(limit).all()
        runs = [db_run_to_evaluation_run(db_run, include_details=False) for db_run in db_runs]

        run_summaries = [
            RunSummary(
                run_id=run["run_id"],
                name=run["name"],
                timestamp=run["timestamp"].isoformat() if run["timestamp"] else "",
                total_documents=run["total_documents"],
                completed_documents=run["completed_documents"],
                error_count=run["error_count"],
                processed_count=run["processed_count"],
                overall_accuracy=round(run["overall_accuracy"] * 100, 1) if run["overall_accuracy"] else 0.0,
                execution_time=round(run["execution_time"], 2) if run["execution_time"] else 0.0,
                status=run["status"],
                document_count=run["completed_documents"],  # Use completed count as documents aren't loaded
                model_name=run["model_name"],
                reasoning_effort=run["reasoning_effort"],
            )
            for run in runs
        ]

        return RunListResponse(runs=run_summaries)
    finally:
        session.close()


@router.get("/stats/by-model")
async def get_model_comparison_stats(
    group_by_reasoning_effort: bool = True,
    session: Session = Depends(get_db_session),
) -> ModelStatsResponse:
    """Get aggregated statistics grouped by model for comparison.

    Calculates aggregate metrics for each model including accuracy, precision,
    recall, F1 score, execution time, and reasoning accuracy. Only includes
    completed runs with ground truth for accuracy statistics.

    Args:
        group_by_reasoning_effort: If True (default), groups by both model_name
            and reasoning_effort. If False, groups by model_name only.
        session: Database session dependency for querying run data.

    Returns:
        ModelStatsResponse containing statistics for each model (and reasoning effort).
    """
    try:
        # Query runs grouped by model_name (and optionally reasoning_effort)
        # Use COALESCE to handle NULL model_name as "Unknown"
        model_name_col = func.coalesce(DBRun.model_name, "Unknown")
        reasoning_effort_col = DBRun.reasoning_effort

        # Define grouping columns based on option
        if group_by_reasoning_effort:
            group_cols = [model_name_col, reasoning_effort_col]
        else:
            group_cols = [model_name_col]

        # Get basic run statistics grouped by model (and effort)
        base_query = session.query(
            model_name_col.label("model_name"),
            reasoning_effort_col.label("reasoning_effort")
            if group_by_reasoning_effort
            else func.literal(None).label("reasoning_effort"),
            func.count(DBRun.id).label("run_count"),
            func.sum(DBRun.total_documents).label("total_documents"),
            func.avg(DBRun.execution_time).label("avg_execution_time"),
            func.max(DBRun.timestamp).label("latest_run_timestamp"),
        ).filter(DBRun.status == RunStatus.COMPLETED.value)

        for col in group_cols:
            base_query = base_query.group_by(col)
        base_stats = base_query.all()

        # Get accuracy stats for runs with ground truth
        accuracy_query = session.query(
            model_name_col.label("model_name"),
            reasoning_effort_col.label("reasoning_effort")
            if group_by_reasoning_effort
            else func.literal(None).label("reasoning_effort"),
            func.avg(DBRun.overall_accuracy).label("avg_accuracy"),
            func.min(DBRun.overall_accuracy).label("min_accuracy"),
            func.max(DBRun.overall_accuracy).label("max_accuracy"),
        ).filter(
            DBRun.status == RunStatus.COMPLETED.value,
            DBRun.has_ground_truth == True,  # noqa: E712
            DBRun.overall_accuracy.isnot(None),
        )
        for col in group_cols:
            accuracy_query = accuracy_query.group_by(col)
        accuracy_stats = accuracy_query.all()

        # Helper to build lookup keys
        def make_key(model_name: str, reasoning_effort: str | None) -> str:
            if group_by_reasoning_effort:
                return f"{model_name}|{reasoning_effort or 'default'}"
            return model_name

        # Calculate precision, recall, F1 from DocumentResult records
        # We need to count TP, FP, FN for each model group
        eval_stats_by_key: dict[str, dict[str, float | None]] = {}

        for row in base_stats:
            key = make_key(row.model_name, row.reasoning_effort)

            # Build filters for this model (and effort)
            filters = [
                func.coalesce(DBRun.model_name, "Unknown") == row.model_name,
                DBRun.status == RunStatus.COMPLETED.value,
            ]
            if group_by_reasoning_effort:
                if row.reasoning_effort is None:
                    filters.append(DBRun.reasoning_effort.is_(None))
                else:
                    filters.append(DBRun.reasoning_effort == row.reasoning_effort)

            # Count confusion matrix values from DocumentResult
            # TP: predicted VALID, expected VALID
            tp = (
                session.query(func.count(DocumentResult.id))
                .join(DBRun, DBRun.id == DocumentResult.run_id)
                .filter(
                    *filters,
                    DocumentResult.predicted_validity == "VALID",
                    DocumentResult.expected_validity == "VALID",
                )
                .scalar()
                or 0
            )

            # FP: predicted VALID, expected INVALID
            fp = (
                session.query(func.count(DocumentResult.id))
                .join(DBRun, DBRun.id == DocumentResult.run_id)
                .filter(
                    *filters,
                    DocumentResult.predicted_validity == "VALID",
                    DocumentResult.expected_validity == "INVALID",
                )
                .scalar()
                or 0
            )

            # FN: predicted INVALID, expected VALID
            fn = (
                session.query(func.count(DocumentResult.id))
                .join(DBRun, DBRun.id == DocumentResult.run_id)
                .filter(
                    *filters,
                    DocumentResult.predicted_validity == "INVALID",
                    DocumentResult.expected_validity == "VALID",
                )
                .scalar()
                or 0
            )

            # Calculate metrics
            precision = tp / (tp + fp) if (tp + fp) > 0 else None
            recall = tp / (tp + fn) if (tp + fn) > 0 else None
            f1_score = (
                (2 * precision * recall / (precision + recall))
                if (precision and recall and (precision + recall) > 0)
                else None
            )

            eval_stats_by_key[key] = {
                "avg_precision": precision,
                "avg_recall": recall,
                "avg_f1_score": f1_score,
            }

        # Get reasoning accuracy stats from document results
        reasoning_query = (
            session.query(
                model_name_col.label("model_name"),
                reasoning_effort_col.label("reasoning_effort")
                if group_by_reasoning_effort
                else func.literal(None).label("reasoning_effort"),
                func.avg(DocumentResult.reasoning_match_score).label("avg_reasoning_accuracy"),
                func.count(DocumentResult.id).label("reasoning_eval_count"),
            )
            .join(DocumentResult, DBRun.id == DocumentResult.run_id)
            .filter(
                DBRun.status == RunStatus.COMPLETED.value,
                DocumentResult.reasoning_evaluated == True,  # noqa: E712
                DocumentResult.reasoning_match_score.isnot(None),
            )
        )
        for col in group_cols:
            reasoning_query = reasoning_query.group_by(col)
        reasoning_stats = reasoning_query.all()

        # Get run_ids for each model (and effort)
        run_ids_query = (
            session.query(
                model_name_col.label("model_name"),
                reasoning_effort_col.label("reasoning_effort")
                if group_by_reasoning_effort
                else func.literal(None).label("reasoning_effort"),
                DBRun.run_id,
            )
            .filter(DBRun.status == RunStatus.COMPLETED.value)
            .all()
        )

        # Build lookup dictionaries using composite key
        accuracy_lookup = {make_key(row.model_name, row.reasoning_effort): row for row in accuracy_stats}
        reasoning_lookup = {make_key(row.model_name, row.reasoning_effort): row for row in reasoning_stats}

        # Group run_ids by model (and effort)
        run_ids_by_key: dict[str, list[str]] = {}
        for row in run_ids_query:
            key = make_key(row.model_name, row.reasoning_effort)
            if key not in run_ids_by_key:
                run_ids_by_key[key] = []
            run_ids_by_key[key].append(row.run_id)

        # Calculate standard deviation for accuracy (since SQLite doesn't support STDDEV)
        std_by_key: dict[str, float | None] = {}
        for row in base_stats:
            key = make_key(row.model_name, row.reasoning_effort)
            filters = [
                func.coalesce(DBRun.model_name, "Unknown") == row.model_name,
                DBRun.status == RunStatus.COMPLETED.value,
                DBRun.has_ground_truth == True,  # noqa: E712
                DBRun.overall_accuracy.isnot(None),
            ]
            if group_by_reasoning_effort:
                if row.reasoning_effort is None:
                    filters.append(DBRun.reasoning_effort.is_(None))
                else:
                    filters.append(DBRun.reasoning_effort == row.reasoning_effort)

            accuracies = session.query(DBRun.overall_accuracy).filter(*filters).all()
            if len(accuracies) > 1:
                values = [a[0] for a in accuracies]
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                std_by_key[key] = variance**0.5
            else:
                std_by_key[key] = None

        # Build response
        model_stats = []
        for row in base_stats:
            key = make_key(row.model_name, row.reasoning_effort)
            acc = accuracy_lookup.get(key)
            eval_data = eval_stats_by_key.get(key, {})
            reasoning_data = reasoning_lookup.get(key)

            model_stats.append(
                ModelStatistics(
                    model_name=row.model_name,
                    reasoning_effort=row.reasoning_effort if group_by_reasoning_effort else None,
                    run_count=row.run_count,
                    total_documents=row.total_documents or 0,
                    avg_accuracy=round(acc.avg_accuracy, 4) if acc and acc.avg_accuracy else None,
                    min_accuracy=round(acc.min_accuracy, 4) if acc and acc.min_accuracy else None,
                    max_accuracy=round(acc.max_accuracy, 4) if acc and acc.max_accuracy else None,
                    std_accuracy=round(std_by_key.get(key), 4) if std_by_key.get(key) else None,
                    avg_execution_time=round(row.avg_execution_time, 2) if row.avg_execution_time else None,
                    avg_precision=round(eval_data.get("avg_precision"), 4) if eval_data.get("avg_precision") else None,
                    avg_recall=round(eval_data.get("avg_recall"), 4) if eval_data.get("avg_recall") else None,
                    avg_f1_score=round(eval_data.get("avg_f1_score"), 4) if eval_data.get("avg_f1_score") else None,
                    avg_reasoning_accuracy=round(reasoning_data.avg_reasoning_accuracy, 4)
                    if reasoning_data and reasoning_data.avg_reasoning_accuracy
                    else None,
                    reasoning_eval_count=reasoning_data.reasoning_eval_count if reasoning_data else 0,
                    latest_run_timestamp=row.latest_run_timestamp.isoformat() if row.latest_run_timestamp else None,
                    run_ids=run_ids_by_key.get(key, []),
                )
            )

        # Sort by run_count descending
        model_stats.sort(key=lambda x: x.run_count, reverse=True)

        return ModelStatsResponse(model_stats=model_stats)
    finally:
        session.close()


@router.get("/{run_id}")
async def get_evaluation_run(run_id: RunID, session: Session = Depends(get_db_session)) -> RunDetailResponse:
    """Retrieve detailed information about a specific evaluation run.

    Fetches comprehensive run data including all documents with reconstructed
    stage information derived from run events. Stage data includes prompts,
    outputs, reasoning, and execution times for classification and validation
    stages.

    Args:
        run_id: Unique identifier of the evaluation run to retrieve.
        session: Database session dependency for querying run data.

    Returns:
        RunDetailResponse containing complete run details with document stages.

    Raises:
        HTTPException: When run_id does not exist in database (404).
    """
    try:
        db_run = get_or_404(session, DBRun, DBRun.run_id == run_id, "Run", run_id)
        run = db_run_to_evaluation_run(db_run, include_details=True)
    finally:
        session.close()

    # Reconstruct documents with stage information from events
    events = run["events"] or []
    documents_with_stages = reconstruct_document_stages(events, run["documents"])

    return RunDetailResponse(
        run_id=run["run_id"],
        timestamp=run["timestamp"].isoformat(),
        total_documents=run["total_documents"],
        completed_documents=run["completed_documents"],
        overall_accuracy=round(run["overall_accuracy"] * 100, 1),
        execution_time=round(run["execution_time"], 2),
        status=run["status"],
        documents=documents_with_stages,
        model_name=run["model_name"],
        reasoning_effort=run["reasoning_effort"],
    )


@router.get("/{run_id}/events")
async def get_run_events(run_id: RunID, session: Session = Depends(get_db_session)) -> RunEventsResponse:
    """Retrieve all events associated with a specific evaluation run.

    Fetches chronological event data for a run, including stage transitions,
    document processing events, and execution details.

    Args:
        run_id: Unique identifier of the evaluation run.
        session: Database session dependency for querying events.

    Returns:
        RunEventsResponse containing list of run events with timestamps and data.

    Raises:
        HTTPException: When run_id does not exist in database (404).
    """
    try:
        db_run = get_or_404(session, DBRun, DBRun.run_id == run_id, "Run", run_id)
        run = db_run_to_evaluation_run(db_run, include_details=True)
        return RunEventsResponse(events=run["events"] or [])
    finally:
        session.close()


@router.patch("/{run_id}")
async def update_evaluation_run(
    run_id: RunID, request: RunUpdateRequest, session: Session = Depends(get_db_session)
) -> RunUpdateResponse:
    """Update metadata for a specific evaluation run.

    Modifies run attributes such as the run name. Changes are persisted to
    the database immediately. Empty or whitespace-only names are stored as None.

    Args:
        run_id: Unique identifier of the evaluation run to update.
        request: Update request containing fields to modify (e.g., name).
        session: Database session dependency for updating run data.

    Returns:
        RunUpdateResponse confirming update with current run metadata.

    Raises:
        HTTPException: When run_id does not exist in database (404).
    """
    try:
        db_run = get_or_404(session, DBRun, DBRun.run_id == run_id, "Run", run_id)

        # Update name if provided
        if request.name is not None:
            db_run.name = request.name.strip() if request.name else None
            session.commit()

        return RunUpdateResponse(status="updated", run_id=run_id, name=db_run.name)
    finally:
        session.close()


@router.delete("/{run_id}")
async def delete_evaluation_run(run_id: RunID, session: Session = Depends(get_db_session)) -> RunDeleteResponse:
    """Delete a specific evaluation run from the database.

    Permanently removes the run and all associated documents and events through
    cascade deletion. This operation cannot be undone.

    Args:
        run_id: Unique identifier of the evaluation run to delete.
        session: Database session dependency for deletion operation.

    Returns:
        RunDeleteResponse confirming successful deletion with run_id.

    Raises:
        HTTPException: When run_id does not exist in database (404).
    """
    try:
        db_run = get_or_404(session, DBRun, DBRun.run_id == run_id, "Run", run_id)

        # Delete the run (cascade will delete related documents and events)
        session.delete(db_run)
        session.commit()

        return RunDeleteResponse(status="deleted", message=f"Run {run_id} deleted successfully")
    finally:
        session.close()


@router.delete("")
async def clear_evaluation_runs(
    session: Session = Depends(get_db_session),
    request: BulkDeleteRequest | None = Body(None),
) -> RunsClearResponse:
    """Clear all evaluation run history or delete specific runs.

    If run_ids are provided in the request body, deletes only those specific runs.
    Otherwise, permanently removes all runs and their associated documents and events.
    This is a bulk deletion operation that cannot be undone.

    Args:
        request: Optional bulk delete request containing run_ids to delete.
        session: Database session dependency for deletion operation.

    Returns:
        RunsClearResponse containing count of deleted runs and confirmation message.
    """
    try:
        if request and request.run_ids:
            # Bulk delete specific runs
            # Note: We delete individually to trigger ORM cascade for related records
            runs_to_delete = session.query(DBRun).filter(DBRun.run_id.in_(request.run_ids)).all()
            runs_deleted = len(runs_to_delete)

            for run in runs_to_delete:
                session.delete(run)

            session.commit()
            logger.info(f"Deleted {runs_deleted} runs with cascade")
            return RunsClearResponse(status="deleted", message=f"Deleted {runs_deleted} evaluation runs")
        else:
            # Count runs before deletion
            runs_deleted = session.query(DBRun).count()

            # Delete all runs (cascade will delete related documents and events)
            session.query(DBRun).delete()
            session.commit()

            return RunsClearResponse(status="cleared", message=f"Deleted {runs_deleted} evaluation runs")
    finally:
        session.close()


@router.get("/{run_id}/export")
async def export_run_json(run_id: RunID, session: Session = Depends(get_db_session)) -> dict[str, Any]:
    """Export comprehensive evaluation run data as structured JSON.

    Generates a complete export of run data including all documents with
    detailed stage information (classification, validation) derived
    from run events. Suitable for external analysis, reporting, or archival.

    Args:
        run_id: Unique identifier of the evaluation run to export.
        session: Database session dependency for querying run data.

    Returns:
        Dictionary containing complete run metadata, document results, and
        stage-specific outputs with prompts, reasoning, and execution metrics.

    Raises:
        HTTPException: When run_id does not exist in database (404).
    """
    try:
        db_run = get_or_404(session, DBRun, DBRun.run_id == run_id, "Run", run_id)

        run = db_run_to_evaluation_run(db_run, include_details=True)

        # Reconstruct stage data from events using shared helper
        events = run["events"] or []
        documents_with_stages = reconstruct_document_stages(events, run["documents"])

        # Build structured JSON with document data and stage details
        export_data = {
            "run_id": run["run_id"],
            "timestamp": run["timestamp"].isoformat(),
            "total_documents": run["total_documents"],
            "completed_documents": run["completed_documents"],
            "overall_accuracy": run["overall_accuracy"],
            "execution_time": run["execution_time"],
            "status": run["status"],
            "model_name": run["model_name"],
            "documents": [],
        }

        # Add document data with stage details
        for doc in documents_with_stages:
            # Get stages from reconstructed data
            stages = doc.get("stages", [])

            # Extract stage-specific data (stages can be identified by number or name)
            classification_stage: dict[str, Any] = next(
                (s for s in stages if s.get("stage") in (1, "classification")), {}
            )
            validation_stage: dict[str, Any] = next((s for s in stages if s.get("stage") in (2, "validation")), {})

            export_data["documents"].append(
                {
                    "document_id": doc.get("document_id", ""),
                    "filename": doc.get("filename", ""),
                    "expected_validity": doc.get("expected_validity", ""),
                    "predicted_validity": doc.get("predicted_validity", ""),
                    "is_correct": doc.get("is_correct"),
                    "confidence": doc.get("confidence"),
                    "prompt_type": doc.get("prompt_type", ""),
                    "execution_time": doc.get("execution_time"),
                    "predicted_reasoning": doc.get("predicted_reasoning", ""),
                    "stages": {
                        "classification": {
                            "output": classification_stage.get("model_output", ""),
                            "reasoning": classification_stage.get("reasoning", ""),
                            "execution_time": classification_stage.get("execution_time"),
                        },
                        "validation": {
                            "output": validation_stage.get("model_output", ""),
                            "reasoning": validation_stage.get("reasoning", ""),
                            "execution_time": validation_stage.get("execution_time"),
                        },
                    },
                }
            )

        return export_data
    finally:
        session.close()
