import asyncio
import logging
from collections.abc import Callable, Coroutine
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.api.constants import EventType, Stage
from backend.api.dependencies import get_app_state, get_session_maker_instance
from backend.api.error_handlers import (
    bad_request,
    conflict,
    handle_error,
    internal_error,
    not_found,
)
from backend.api.models.requests import EvaluationRequest
from backend.api.models.responses import (
    CurrentRunResponse,
    EvaluationStartResponse,
    StatusResponse,
)
from backend.api.websocket import manager
from backend.config import EvaluationConfig
from backend.database.repositories.run_persistence import RunPersistenceService
from backend.models import GroundTruthDocument
from backend.models_config import get_model_by_id
from backend.services.loaders import (
    load_ground_truth_dataset,
    scan_documents_for_testing,
)
from backend.services.pipeline_evaluator import Evaluator
from backend.state import AppState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["evaluation"])


# ============================================================================
# Helper Functions for Stage Callback
# ============================================================================


async def _broadcast_and_save_stage_started(
    document_id: str,
    stage: Stage,
    run_id: str,
    persistence: RunPersistenceService,
    save_events: bool,
) -> None:
    """Broadcast and optionally save stage started event.

    Args:
        document_id: Document identifier
        stage: Stage being started
        run_id: Run identifier
        persistence: Persistence service
        save_events: Whether to save events to database
    """
    event_data = {
        "document_id": document_id,
        "stage": stage.value,
    }
    await manager.broadcast(
        {
            "type": EventType.STAGE_STARTED.value,
            "data": event_data,
        }
    )
    if save_events:
        persistence.save_event(
            run_id=run_id,
            event_type=EventType.STAGE_STARTED.value,
            document_id=document_id,
            data=event_data,
        )


def _prepare_classification_broadcast_data(document_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Prepare broadcast data for classification stage.

    Args:
        document_id: Document identifier
        data: Stage data from evaluator

    Returns:
        Formatted broadcast data
    """
    import json

    broadcast_data = {
        "document_id": document_id,
        "stage": "classification",
    }

    doc_type = data.get("document_type")
    confidence = data.get("confidence")
    reasoning = data.get("reasoning")
    raw_response = data.get("raw_response")

    # Include raw Pydantic model as JSON for AI Response section
    if raw_response:
        broadcast_data["model_output"] = json.dumps(raw_response.model_dump(), indent=2)
        broadcast_data["json_data"] = raw_response.model_dump()
    else:
        # Fallback to formatted output
        model_output = f"Document Type: {doc_type}"
        if confidence:
            model_output += f"\nConfidence: {confidence}"
        broadcast_data["model_output"] = model_output

    # Include reasoning separately for "Decision Explanation" section
    if reasoning:
        broadcast_data["reasoning"] = reasoning

    return broadcast_data


def _prepare_validation_broadcast_data(document_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Prepare broadcast data for validation stage.

    Args:
        document_id: Document identifier
        data: Stage data from evaluator

    Returns:
        Formatted broadcast data
    """
    import json
    from typing import Any

    broadcast_data: dict[str, Any] = {
        "document_id": document_id,
        "stage": "validation",
    }

    validity = data.get("validity_assessment")
    reasoning: str = data.get("reasoning", "")
    confidence: str = data.get("confidence", "LOW")
    raw_response = data.get("raw_response")
    is_composite = data.get("is_composite", False)
    constituent_validations = data.get("constituent_validations", [])

    # Include raw response as JSON for AI Response section
    if raw_response:
        if isinstance(raw_response, dict):
            # Mixed plans composite response
            broadcast_data["model_output"] = json.dumps(raw_response, indent=2)
            broadcast_data["json_data"] = raw_response
        else:
            # Standard Pydantic model response
            broadcast_data["model_output"] = json.dumps(raw_response.model_dump(), indent=2)
            broadcast_data["json_data"] = raw_response.model_dump()
    else:
        # Fallback to formatted output
        broadcast_data["model_output"] = (
            f"Validity Assessment: {validity}\nConfidence: {confidence}"
            if validity and confidence
            else "Validation complete"
        )

    broadcast_data["reasoning"] = reasoning
    broadcast_data["confidence"] = confidence
    broadcast_data["is_composite"] = is_composite

    # Include constituent validations for mixed plans
    if is_composite and constituent_validations:
        broadcast_data["constituent_validations"] = constituent_validations

    return broadcast_data


def create_stage_callback(
    run_id: str, persistence: RunPersistenceService, save_events: bool = True
) -> Callable[[str, str, dict[str, Any]], Coroutine[Any, Any, None]]:
    """Create a stage callback that saves events to database.

    Args:
        run_id: Run identifier for event persistence
        persistence: Persistence service for saving events
        save_events: Whether to save events to database

    Returns:
        Async callback function for stage completion
    """

    async def stage_completed_callback(stage: str, document_id: str, data: dict[str, Any]) -> None:
        """Callback invoked by evaluator when each stage completes or starts.

        Args:
            stage: Stage name (classification, validation, validation_started)
            document_id: Document being evaluated
            data: Stage-specific data to broadcast
        """
        # Handle stage_started messages
        if stage == "validation_started":
            await _broadcast_and_save_stage_started(document_id, Stage.VALIDATION, run_id, persistence, save_events)
            return

        # Handle stage_completed messages - prepare broadcast data based on stage type
        if stage == "classification":
            broadcast_data = _prepare_classification_broadcast_data(document_id, data)
        elif stage == "validation":
            broadcast_data = _prepare_validation_broadcast_data(document_id, data)
        else:
            # Unknown stage - use basic format
            broadcast_data = {
                "document_id": document_id,
                "stage": stage,
            }

        # Broadcast and save event
        await manager.broadcast(
            {
                "type": EventType.STAGE_COMPLETED.value,
                "data": broadcast_data,
            }
        )

        if save_events:
            persistence.save_event(
                run_id=run_id,
                event_type=EventType.STAGE_COMPLETED.value,
                document_id=document_id,
                data=broadcast_data,
            )

    return stage_completed_callback


# ============================================================================
# Helper Functions for Evaluation Loop
# ============================================================================


async def _evaluate_single_document(
    doc: GroundTruthDocument,
    idx: int,
    total: int,
    evaluator: Evaluator,
    run_id: str,
    persistence: RunPersistenceService,
    semaphore: asyncio.Semaphore,
    queue_tracking: dict[str, Any],
) -> dict[str, Any] | None:
    """Evaluate a single document with queue tracking and broadcasting.

    Args:
        doc: Ground truth document to evaluate
        idx: Document index (1-based)
        total: Total number of documents
        evaluator: Evaluator instance
        run_id: Run identifier
        persistence: Persistence service
        semaphore: Concurrency control semaphore
        queue_tracking: Dictionary tracking queued/processing/completed counts

    Returns:
        Result dictionary if successful, None if error occurred
    """
    async with semaphore:
        # Update queue status: move from queued to processing
        queue_tracking["queued"] -= 1
        queue_tracking["processing"] += 1

        await manager.broadcast(
            {
                "type": EventType.QUEUE_STATUS.value,
                "data": {
                    "queued": queue_tracking["queued"],
                    "processing": queue_tracking["processing"],
                    "completed": queue_tracking["completed"],
                    "total": total,
                },
            }
        )

        try:
            # Broadcast document start
            expected_validity = doc.expected_validity if doc.expected_validity != "UNKNOWN" else None
            logger.info(
                f"Broadcasting document_started for {doc.document.document_id}: expected_validity={doc.expected_validity}"
            )
            await manager.broadcast(
                {
                    "type": EventType.DOCUMENT_STARTED.value,
                    "data": {
                        "document_id": doc.document.document_id,
                        "filename": doc.document.filename,
                        "expected_validity": expected_validity,
                        "progress": f"{idx}/{total}",
                    },
                }
            )

            # Broadcast stage: classification started
            await manager.broadcast(
                {
                    "type": EventType.STAGE_STARTED.value,
                    "data": {
                        "document_id": doc.document.document_id,
                        "stage": Stage.CLASSIFICATION.value,
                    },
                }
            )

            # Evaluate (stage_completed broadcasts happen via callback)
            result = await evaluator.evaluate(doc)

            # Log if evaluation returned ERROR
            if result.predicted_validity == "ERROR":
                logger.error(
                    f"Evaluation returned ERROR for {doc.document.document_id}: "
                    f"success={result.success}, error_message={result.error_message}"
                )

            # Save to database
            persistence.save_document_result(
                run_id=run_id,
                document_id=result.document_id,
                filename=doc.document.filename,
                result_data={
                    "predicted_validity": result.predicted_validity,
                    "predicted_reasoning": result.predicted_reasoning,
                    "expected_validity": result.ground_truth_validity,
                    "correct": result.correct,
                    "confidence": result.confidence,
                    "prompt_type": result.prompt_type,
                    "execution_time": result.execution_time,
                    "carbon_impact": result.carbon_impact,
                    "reasoning_match_score": result.reasoning_match_score,
                    "reasoning_evaluated": result.reasoning_evaluated,
                    "reasoning_explanation": result.reasoning_explanation,
                    "ground_truth_reason": doc.expected_reasoning,
                },
            )

            # Serialize carbon_impact to dict for JSON transmission
            carbon_impact_dict = None
            if result.carbon_impact:
                carbon_impact_dict = {
                    "energy_kwh_min": result.carbon_impact.energy_kwh_min,
                    "energy_kwh_max": result.carbon_impact.energy_kwh_max,
                    "gwp_kgco2eq_min": result.carbon_impact.gwp_kgco2eq_min,
                    "gwp_kgco2eq_max": result.carbon_impact.gwp_kgco2eq_max,
                    "adpe_kgsbeq_min": result.carbon_impact.adpe_kgsbeq_min,
                    "adpe_kgsbeq_max": result.carbon_impact.adpe_kgsbeq_max,
                    "pe_mj_min": result.carbon_impact.pe_mj_min,
                    "pe_mj_max": result.carbon_impact.pe_mj_max,
                    "wcf_l_min": result.carbon_impact.wcf_l_min,
                    "wcf_l_max": result.carbon_impact.wcf_l_max,
                }

            # Broadcast completion
            await manager.broadcast(
                {
                    "type": EventType.DOCUMENT_COMPLETED.value,
                    "data": {
                        "document_id": doc.document.document_id,
                        "status": "completed",  # Explicitly set status
                        "result": {
                            "predicted_validity": result.predicted_validity,
                            "predicted_reasoning": result.predicted_reasoning,
                            "confidence": result.confidence,
                            "correct": result.correct,
                            "execution_time": result.execution_time,
                            "prompt_type": result.prompt_type,
                            "carbon_impact": carbon_impact_dict,
                            "reasoning_match_score": result.reasoning_match_score,
                            "reasoning_evaluated": result.reasoning_evaluated,
                            "reasoning_explanation": result.reasoning_explanation,
                        },
                        "progress": f"{idx}/{total}",
                    },
                }
            )

            # Update queue status: move from processing to completed
            queue_tracking["processing"] -= 1
            queue_tracking["completed"] += 1

            # Update run progress in database
            persistence.update_run_status(
                run_id=run_id,
                status="running",
                completed_documents=queue_tracking["completed"],
            )

            await manager.broadcast(
                {
                    "type": EventType.QUEUE_STATUS.value,
                    "data": {
                        "queued": queue_tracking["queued"],
                        "processing": queue_tracking["processing"],
                        "completed": queue_tracking["completed"],
                        "total": total,
                    },
                }
            )

            return {
                "document_id": result.document_id,
                "predicted_validity": result.predicted_validity,
                "confidence": result.confidence,
                "correct": result.correct,
                "execution_time": result.execution_time,
            }

        except Exception as e:
            logger.exception(f"Error evaluating {doc.document.document_id}")
            # Move from processing to completed (even on error)
            queue_tracking["processing"] -= 1
            queue_tracking["completed"] += 1

            # Update run progress in database (even on error)
            persistence.update_run_status(
                run_id=run_id,
                status="running",
                completed_documents=queue_tracking["completed"],
            )

            await manager.broadcast(
                {
                    "type": EventType.DOCUMENT_ERROR.value,
                    "data": {
                        "document_id": doc.document.document_id,
                        "error": str(e),
                    },
                }
            )

            await manager.broadcast(
                {
                    "type": EventType.QUEUE_STATUS.value,
                    "data": {
                        "queued": queue_tracking["queued"],
                        "processing": queue_tracking["processing"],
                        "completed": queue_tracking["completed"],
                        "total": total,
                    },
                }
            )

            return None


async def run_evaluation_loop(
    documents: list[GroundTruthDocument],
    evaluator: Evaluator,
    run_id: str,
    persistence: RunPersistenceService,
    max_concurrent: int = EvaluationConfig.MAX_CONCURRENT_DOCUMENTS,
    save_events: bool = True,
) -> list[dict[str, Any]]:
    """Concurrent evaluation loop - process documents with controlled concurrency.

    Args:
        documents: Documents to evaluate
        evaluator: Evaluator instance
        run_id: Unique run identifier
        persistence: Database persistence service
        max_concurrent: Maximum number of concurrent evaluations
        save_events: Whether to save events to database

    Returns:
        List of evaluation results
    """
    total = len(documents)
    eval_start_time = datetime.now()

    # Queue tracking state shared across all evaluations
    queue_tracking = {
        "queued": total,
        "processing": 0,
        "completed": 0,
    }

    # Semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)

    # Broadcast evaluation start
    await manager.broadcast(
        {
            "type": EventType.EVALUATION_STARTED.value,
            "data": {
                "run_id": run_id,
                "total_documents": total,
                "queued": queue_tracking["queued"],
                "processing": queue_tracking["processing"],
                "completed": queue_tracking["completed"],
                "max_concurrent": max_concurrent,
                "message": "Starting evaluation",
                "documents": [
                    {
                        "document_id": doc.document.document_id,
                        "filename": doc.document.filename,
                    }
                    for doc in documents
                ],
            },
        }
    )

    # Evaluate all documents concurrently
    tasks = [
        _evaluate_single_document(doc, idx, total, evaluator, run_id, persistence, semaphore, queue_tracking)
        for idx, doc in enumerate(documents, 1)
    ]
    task_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out None results (errors) and collect successful results
    from typing import Any

    results: list[dict[str, Any]] = []
    for r in task_results:
        if r is not None and not isinstance(r, Exception):
            # Type narrowing: r is dict[str, Any] here (not None or Exception)
            assert isinstance(r, dict)
            results.append(r)

    # Calculate final metrics
    eval_end_time = datetime.now()
    total_execution_time = (eval_end_time - eval_start_time).total_seconds()

    correct_count = sum(1 for r in results if r.get("correct") is True)
    accuracy = (correct_count / total) if total > 0 else 0.0
    accuracy_percent = accuracy * 100

    # Update run status to completed
    persistence.update_run_status(
        run_id=run_id,
        status="completed",
        completed_documents=queue_tracking["completed"],
        overall_accuracy=accuracy,
        execution_time=total_execution_time,
    )
    logger.info(
        f"Evaluation completed: {queue_tracking['completed']}/{total} docs, "
        f"accuracy={accuracy_percent:.1f}%, time={total_execution_time:.2f}s"
    )

    # Broadcast completion
    await manager.broadcast(
        {
            "type": EventType.EVALUATION_COMPLETED.value,
            "data": {
                "run_id": run_id,
                "total_documents": total,
                "accuracy": accuracy_percent,
                "results": results,
            },
        }
    )

    return results


# ============================================================================
# Helper Functions for Start Evaluation
# ============================================================================


def _enrich_documents_with_ground_truth(
    documents: list[GroundTruthDocument],
    gt_records: list[GroundTruthDocument],
) -> int:
    """Enrich documents with ground truth data using exact and basename matching.

    Args:
        documents: Documents to enrich
        gt_records: Ground truth records to match against

    Returns:
        Number of documents successfully enriched
    """
    # Create two maps: exact match and basename match (for handling .pdf vs .jpg)
    gt_map_exact = {gt.document.filename: gt for gt in gt_records}
    gt_map_basename = {Path(gt.document.filename).stem: gt for gt in gt_records}

    enriched_count = 0
    for doc in documents:
        # Try exact match first, then fall back to basename match
        gt = gt_map_exact.get(doc.document.filename)
        if not gt:
            # Try matching by basename without extension
            doc_basename = Path(doc.document.filename).stem
            gt = gt_map_basename.get(doc_basename)

        if gt:
            # Update the document's expected validity and reasoning
            doc.expected_validity = gt.expected_validity
            doc.expected_reasoning = gt.expected_reasoning
            enriched_count += 1

    logger.info(f"Enriched {enriched_count}/{len(documents)} documents with ground truth")
    return enriched_count


def _determine_run_id(scan_storage_prefix: str | None) -> str:
    """Determine run ID from S3 prefix or generate new one.

    Args:
        scan_storage_prefix: S3 prefix to extract run ID from

    Returns:
        Run ID (either extracted from S3 or newly generated)
    """
    start_time = datetime.now()
    if scan_storage_prefix and "/" in scan_storage_prefix:
        # Extract run_id from storage_prefix format: "runs/run_TIMESTAMP"
        run_id = scan_storage_prefix.split("/")[-1]
        logger.info(f"Reusing existing run_id from S3 prefix: {run_id}")
    else:
        # Generate new run_id for standalone evaluation (rare case)
        run_id = f"run_{start_time.strftime('%Y%m%d_%H%M%S')}_{start_time.microsecond:06d}"
        logger.info(f"Generated new run_id: {run_id}")
    return run_id


@router.post("/start-evaluation")
async def start_evaluation(
    request: EvaluationRequest | None = None,
    state: AppState = Depends(get_app_state),
) -> EvaluationStartResponse:
    """Start document evaluation run.

    Args:
        request: Optional evaluation configuration
        state: Application state

    Returns:
        Evaluation start confirmation with run ID

    Raises:
        HTTPException: 409 if evaluation already running
        HTTPException: 400 if no documents found
    """
    if state.is_evaluation_running():
        raise conflict("Evaluation already running")

    try:
        # Log request parameters
        logger.info(f"Start evaluation request: {request}")
        if request:
            logger.info(
                f"Request params - ground_truth_path: {request.ground_truth_path}, skip_ground_truth: {getattr(request, 'skip_ground_truth', None)}, model_name: {getattr(request, 'model_name', None)}"
            )

        # Extract model_name from request
        model_name = request.model_name if request else None
        logger.info(f"[MODEL TRACE] Extracted model_name from request: {model_name}")

        # Apply request parameters
        if request:
            if request.concurrency:
                state.set_doc_concurrency(request.concurrency)
            if request.data_dir:
                state.set_data_source_local(Path(request.data_dir))

        # Determine S3 prefix for scanning
        # If ground truth path is provided, use its prefix to ensure documents and GT are from same run
        scan_storage_prefix = state.current_storage_prefix
        logger.info(f"Initial scan_storage_prefix from state: {scan_storage_prefix}")

        if request and request.ground_truth_path:
            # Extract storage_prefix from ground_truth_path (format: runs/run_TIMESTAMP/ground_truth.json)
            if "/" in request.ground_truth_path:
                scan_storage_prefix = request.ground_truth_path.rsplit("/", 1)[0]
                logger.info(
                    f"Extracted S3 prefix from ground truth path '{request.ground_truth_path}': {scan_storage_prefix}"
                )

        logger.info(f"Final scan_storage_prefix for document scanning: {scan_storage_prefix}")

        # Scan documents
        logger.debug(
            f"Scanning documents with scan_storage_prefix={scan_storage_prefix}, data_dir={state.current_data_dir}"
        )
        if scan_storage_prefix:
            logger.debug(f"Calling scan_documents with storage_prefix={scan_storage_prefix}")
            documents = scan_documents_for_testing(data_dir=None, storage_prefix=scan_storage_prefix)
        else:
            logger.debug(f"Calling scan_documents with data_dir={state.current_data_dir}")
            documents = scan_documents_for_testing(data_dir=state.current_data_dir, storage_prefix=None)

        if not documents:
            raise bad_request("No documents found for evaluation")

        # Load ground truth if available
        # If no explicit path provided, try to find ground truth in the S3 run directory
        gt_path = None
        if request and request.ground_truth_path:
            gt_path = request.ground_truth_path
        elif scan_storage_prefix and not (request and request.skip_ground_truth):
            # Try default ground truth location in S3 run
            gt_path = f"{scan_storage_prefix}/ground_truth.json"
            logger.info(f"No explicit ground_truth_path provided, trying default location: {gt_path}")

        if gt_path and not (request and request.skip_ground_truth):
            try:
                # Convert Pydantic ColumnConfig to dict for loader
                column_config_dict = None
                if request and request.column_config:
                    column_config_dict = {
                        "filename": request.column_config.filename,
                        "validity": request.column_config.validity,
                        "reason": request.column_config.reason,
                    }

                logger.info(f"Loading ground truth from: {gt_path} with column_config={column_config_dict}")
                gt_records = load_ground_truth_dataset(
                    ground_truth_path=gt_path,
                    storage_prefix=scan_storage_prefix,
                    data_dir=state.current_data_dir,
                    column_config=column_config_dict,
                )
                logger.info(f"Loaded {len(gt_records)} ground truth records")
                _enrich_documents_with_ground_truth(documents, gt_records)
            except Exception as e:
                logger.exception(f"Failed to load ground truth: {e}")

        # Apply filters
        if request:
            if request.document_ids:
                documents = [d for d in documents if d.document.filename in request.document_ids]
            if request.max_samples:
                documents = documents[: request.max_samples]

        # Always generate a new run_id for each evaluation
        # This ensures every evaluation is a separate run, even with same data/model
        start_time = datetime.now()
        timestamp_suffix = start_time.strftime("%Y%m%d_%H%M%S%f")
        run_id = f"run_{timestamp_suffix}"
        logger.info(f"Creating new evaluation run: {run_id}")

        # Create persistence service
        persistence = RunPersistenceService(get_session_maker_instance())

        # Check if run has ground truth
        has_ground_truth = any(d.expected_validity and d.expected_validity.upper() != "UNKNOWN" for d in documents)

        # Determine reasoning_effort: use request override if provided, otherwise fall back to model config default
        # Only apply if the model supports reasoning (defaults to True if not specified)
        model_config = get_model_by_id(model_name) if model_name else None
        supports_reasoning = model_config.get("supports_reasoning", True) if model_config else True

        if supports_reasoning:
            model_default_reasoning = model_config.get("reasoning_effort") if model_config else None
            reasoning_effort = (
                request.reasoning_effort if request and request.reasoning_effort else model_default_reasoning
            )
        else:
            # Model doesn't support reasoning params - don't send them
            reasoning_effort = None
            if request and request.reasoning_effort:
                logger.info(f"Model {model_name} doesn't support reasoning_effort, ignoring request value")

        # Check if model requires PDF-to-image conversion (e.g., Azure-hosted OpenAI models)
        convert_pdf_to_images = model_config.get("convert_pdf_to_images", False) if model_config else False

        # Create new run record in database
        logger.info(
            f"Creating new run {run_id} in database with {len(documents)} documents, model={model_name}, reasoning_effort={reasoning_effort}, convert_pdf_to_images={convert_pdf_to_images}"
        )
        persistence.create_run(
            run_id=run_id,
            timestamp=start_time,
            total_documents=len(documents),
            has_ground_truth=has_ground_truth,
            model_name=model_name,
            reasoning_effort=reasoning_effort,
        )

        # Create stage callback with persistence
        stage_callback = create_stage_callback(run_id, persistence, save_events=True)

        evaluator = Evaluator(
            max_concurrent=request.concurrency if request else None,
            storage_prefix=scan_storage_prefix,
            stage_callback=stage_callback,
            run_id=run_id,
            model_name=model_name,
            reasoning_effort=reasoning_effort,
            convert_pdf_to_images=convert_pdf_to_images,
        )

        # Store current evaluation details in state
        state.current_evaluation = {
            "run_id": run_id,
            "total_documents": len(documents),
            "completed_documents": 0,
            "documents": [
                {
                    "document_id": doc.document.document_id,
                    "filename": doc.document.filename,
                }
                for doc in documents
            ],
        }

        # Start evaluation in background
        async def run_task() -> None:
            try:
                max_concurrent = (
                    request.concurrency
                    if request and request.concurrency
                    else EvaluationConfig.MAX_CONCURRENT_DOCUMENTS
                )
                await run_evaluation_loop(
                    documents,
                    evaluator,
                    run_id,
                    persistence,
                    max_concurrent=max_concurrent,
                )
            finally:
                state.evaluation_task = None
                state.current_evaluation = None

        state.evaluation_task = asyncio.create_task(run_task())

        return EvaluationStartResponse(
            status="started",
            message=f"Evaluation started with {len(documents)} documents",
            run_id=run_id,
            total_documents=len(documents),
            model_name=model_name,
            reasoning_effort=reasoning_effort,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise handle_error(e, context={"operation": "start_evaluation"})


@router.get("/status")
async def get_status(state: AppState = Depends(get_app_state)) -> StatusResponse:
    """Get current evaluation status.

    Args:
        state: Application state

    Returns:
        Status information
    """
    is_running = state.is_evaluation_running()
    return StatusResponse(
        status="running" if is_running else "idle",
        message="Evaluation running" if is_running else "No evaluation running",
    )


@router.get("/current-run")
async def get_current_run(
    state: AppState = Depends(get_app_state),
) -> CurrentRunResponse:
    """Get current run information.

    Args:
        state: Application state

    Returns:
        Current run details or empty response

    Raises:
        HTTPException: 404 if no evaluation running
    """
    if not state.is_evaluation_running():
        raise not_found("Active evaluation")

    if not state.current_evaluation:
        raise internal_error("Evaluation running but no run details available")

    return CurrentRunResponse(
        status="running",
        run_id=state.current_evaluation["run_id"],
        total_documents=state.current_evaluation["total_documents"],
        completed_documents=state.current_evaluation["completed_documents"],
        documents=state.current_evaluation["documents"],
    )


@router.post("/stop-evaluation")
async def stop_evaluation(state: AppState = Depends(get_app_state)) -> StatusResponse:
    """Stop current evaluation.

    Args:
        state: Application state

    Returns:
        Stop confirmation

    Raises:
        HTTPException: 404 if no evaluation running
    """
    if not state.is_evaluation_running():
        raise not_found("Active evaluation")

    # Cancel task
    if state.evaluation_task and not state.evaluation_task.done():
        state.evaluation_task.cancel()

    # Note: We don't update run status to "cancelled" here because we don't have the run_id
    # The run will remain in "running" status if stopped mid-evaluation
    # This is acceptable as users can still see partial results and resume if needed

    # Broadcast stop message
    await manager.broadcast(
        {
            "type": EventType.EVALUATION_STOPPED.value,
            "data": {"message": "Evaluation stopped by user"},
        }
    )

    state.evaluation_task = None

    return StatusResponse(
        status="stopped",
        message="Evaluation stopped",
    )
