import logging
from datetime import UTC, datetime
from typing import Any

from planning_drawing_validator.types import DocumentID, EventType, Filename, RunID
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, sessionmaker

from backend.api.constants import RunStatus
from backend.api.models.responses import EvaluationRun
from backend.config import PaginationConfig
from backend.database.models import (
    DocumentResult as DBDocumentResult,
    Run as DBRun,
    RunEvent as DBRunEvent,
)

__all__ = ["RunPersistenceService"]

logger = logging.getLogger(__name__)


class RunPersistenceService:
    """Service for persisting and retrieving evaluation runs from the database.

    Handles all database operations for evaluation runs including:
    - Creating and updating run records
    - Storing document results and events
    - Querying run history
    - Converting between API and database models
    """

    def __init__(self, session_maker: sessionmaker[Session]) -> None:
        """Initialise the persistence service.

        Args:
            session_maker: SQLAlchemy session maker function
        """
        self.session_maker = session_maker

    def create_run(
        self,
        run_id: RunID,
        timestamp: datetime,
        total_documents: int,
        has_ground_truth: bool,
        name: str | None = None,
        model_name: str | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        """Create a new evaluation run in the database.

        Args:
            run_id: Unique run identifier
            timestamp: Run start timestamp
            total_documents: Total number of documents to evaluate
            has_ground_truth: Whether ground truth labels are available
            name: Optional user-defined run name
            model_name: Optional LiteLLM model identifier
            reasoning_effort: Optional reasoning/thinking level ("none", "low", "medium", "high")
        """
        with self.session_maker() as session:
            try:
                logger.info(
                    f"[MODEL TRACE] About to create run {run_id} with model_name={model_name}, reasoning_effort={reasoning_effort}"
                )
                db_run = DBRun(
                    run_id=run_id,
                    name=name,
                    timestamp=timestamp,
                    total_documents=total_documents,
                    completed_documents=0,
                    overall_accuracy=0.0,
                    execution_time=0.0,
                    status=RunStatus.RUNNING.value,
                    has_ground_truth=has_ground_truth,
                    data_dir=None,  # Using S3 storage
                    model_name=model_name,
                    reasoning_effort=reasoning_effort,
                )
                session.add(db_run)
                session.commit()
                logger.info(
                    f"Created run {run_id} in database with model_name={db_run.model_name}, reasoning_effort={db_run.reasoning_effort}"
                )
            except Exception as e:
                logger.error(f"Failed to create run {run_id}: {e}")
                session.rollback()
                raise

    def update_run_status(
        self,
        run_id: RunID,
        status: str,
        completed_documents: int | None = None,
        total_documents: int | None = None,
        overall_accuracy: float | None = None,
        execution_time: float | None = None,
    ) -> None:
        """Update run status and metrics.

        Args:
            run_id: Run identifier
            status: New status (use RunStatus enum: RUNNING, COMPLETED, CANCELLED, ERROR)
            completed_documents: Number of completed documents (optional)
            total_documents: Total number of documents in run (optional)
            overall_accuracy: Overall accuracy metric (optional)
            execution_time: Total execution time in seconds (optional)
        """
        with self.session_maker() as session:
            try:
                stmt = select(DBRun).where(DBRun.run_id == run_id)
                db_run = session.scalars(stmt).first()
                if not db_run:
                    logger.warning(f"Run {run_id} not found for update")
                    return

                db_run.status = status
                if completed_documents is not None:
                    db_run.completed_documents = completed_documents
                if total_documents is not None:
                    db_run.total_documents = total_documents
                if overall_accuracy is not None:
                    db_run.overall_accuracy = overall_accuracy
                if execution_time is not None:
                    db_run.execution_time = execution_time

                session.commit()
                logger.info(f"Updated run {run_id} status to {status}")
            except Exception as e:
                logger.error(f"Failed to update run {run_id}: {e}")
                session.rollback()
                raise

    def run_exists(self, run_id: RunID) -> bool:
        """Check if a run exists in the database.

        Args:
            run_id: Run identifier

        Returns:
            True if run exists, False otherwise
        """
        with self.session_maker() as session:
            try:
                stmt = select(DBRun).where(DBRun.run_id == run_id)
                db_run = session.scalars(stmt).first()
                return db_run is not None
            except Exception as e:
                logger.error(f"Failed to check if run {run_id} exists: {e}")
                return False

    def update_run_ground_truth_status(self, run_id: RunID, has_ground_truth: bool) -> None:
        """Update the has_ground_truth flag for a run.

        Args:
            run_id: Run identifier
            has_ground_truth: Whether ground truth is available
        """
        with self.session_maker() as session:
            try:
                stmt = select(DBRun).where(DBRun.run_id == run_id)
                db_run = session.scalars(stmt).first()
                if not db_run:
                    logger.warning(f"Run {run_id} not found for ground truth update")
                    return

                db_run.has_ground_truth = has_ground_truth
                session.commit()
                logger.info(f"Updated run {run_id} has_ground_truth to {has_ground_truth}")
            except Exception as e:
                logger.error(f"Failed to update run {run_id} ground truth status: {e}")
                session.rollback()
                raise

    def save_document_result(
        self,
        run_id: RunID,
        document_id: DocumentID,
        filename: Filename,
        result_data: dict[str, Any],
    ) -> None:
        """Save a document evaluation result.

        Args:
            run_id: Run identifier (string like "run_20251014_102158")
            document_id: Document identifier
            filename: Document filename
            result_data: Dictionary containing evaluation results
        """
        with self.session_maker() as session:
            try:
                # Look up the Run record to get the integer ID
                stmt = select(DBRun).where(DBRun.run_id == run_id)
                db_run = session.scalars(stmt).first()
                if not db_run:
                    raise ValueError(f"Run {run_id} not found in database")

                # Extract carbon impact data if present
                carbon_impact = result_data.get("carbon_impact")
                carbon_kwargs = {}
                if carbon_impact:
                    carbon_kwargs = {
                        "carbon_energy_kwh_min": carbon_impact.energy_kwh_min,
                        "carbon_energy_kwh_max": carbon_impact.energy_kwh_max,
                        "carbon_gwp_kgco2eq_min": carbon_impact.gwp_kgco2eq_min,
                        "carbon_gwp_kgco2eq_max": carbon_impact.gwp_kgco2eq_max,
                        "carbon_adpe_kgsbeq_min": carbon_impact.adpe_kgsbeq_min,
                        "carbon_adpe_kgsbeq_max": carbon_impact.adpe_kgsbeq_max,
                        "carbon_pe_mj_min": carbon_impact.pe_mj_min,
                        "carbon_pe_mj_max": carbon_impact.pe_mj_max,
                        "carbon_wcf_l_min": carbon_impact.wcf_l_min,
                        "carbon_wcf_l_max": carbon_impact.wcf_l_max,
                    }

                db_result = DBDocumentResult(
                    run_id=db_run.id,  # Use the integer ID, not the string run_id
                    document_id=document_id,
                    filename=filename,
                    predicted_validity=result_data.get("predicted_validity"),
                    predicted_reasoning=result_data.get("predicted_reasoning"),
                    expected_validity=result_data.get("expected_validity"),
                    is_correct=result_data.get("correct"),
                    confidence=result_data.get("confidence"),
                    prompt_type=result_data.get("prompt_type"),
                    execution_time=result_data.get("execution_time"),
                    stages=result_data.get("stages"),
                    # Reasoning evaluation fields
                    reasoning_match_score=result_data.get("reasoning_match_score"),
                    reasoning_evaluated=result_data.get("reasoning_evaluated", False),
                    reasoning_explanation=result_data.get("reasoning_explanation"),
                    expected_reasoning=result_data.get("ground_truth_reason"),
                    **carbon_kwargs,  # Add carbon impact fields if present
                )
                session.add(db_result)
                session.commit()
                logger.debug(f"Saved result for document {document_id} in run {run_id}")
            except Exception as e:
                logger.error(f"Failed to save document result {document_id}: {e}")
                session.rollback()
                raise

    def get_run(self, run_id: RunID) -> EvaluationRun | None:
        """Retrieve a complete run with all results.

        Uses eager loading to prevent N+1 query issues by loading
        all related documents and events in a single query.

        Args:
            run_id: Run identifier

        Returns:
            EvaluationRun instance or None if not found
        """
        with self.session_maker() as session:
            try:
                # Use eager loading to fetch all relationships in one query
                stmt = (
                    select(DBRun)
                    .where(DBRun.run_id == run_id)
                    .options(
                        joinedload(DBRun.documents),
                        joinedload(DBRun.events),
                    )
                )
                db_run = session.scalars(stmt).first()
                if not db_run:
                    return None

                # Build documents list
                documents = []
                for doc in db_run.documents:
                    doc_dict: dict[str, Any] = {
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
                    }

                    # Include carbon impact data if present
                    if doc.carbon_energy_kwh_min is not None:
                        doc_dict["carbon_impact"] = {
                            "energy_kwh_min": doc.carbon_energy_kwh_min,
                            "energy_kwh_max": doc.carbon_energy_kwh_max,
                            "gwp_kgco2eq_min": doc.carbon_gwp_kgco2eq_min,
                            "gwp_kgco2eq_max": doc.carbon_gwp_kgco2eq_max,
                            "adpe_kgsbeq_min": doc.carbon_adpe_kgsbeq_min,
                            "adpe_kgsbeq_max": doc.carbon_adpe_kgsbeq_max,
                            "pe_mj_min": doc.carbon_pe_mj_min,
                            "pe_mj_max": doc.carbon_pe_mj_max,
                            "wcf_l_min": doc.carbon_wcf_l_min,
                            "wcf_l_max": doc.carbon_wcf_l_max,
                        }

                    # Include reasoning evaluation data if present
                    if doc.reasoning_evaluated:
                        doc_dict["reasoning_match_score"] = doc.reasoning_match_score
                        doc_dict["reasoning_evaluated"] = doc.reasoning_evaluated
                        doc_dict["reasoning_explanation"] = doc.reasoning_explanation
                        doc_dict["expected_reasoning"] = doc.expected_reasoning

                    documents.append(doc_dict)

                # Build events list
                events = []
                for event in db_run.events:
                    events.append(
                        {
                            "event_type": event.event_type,
                            "timestamp": event.timestamp.isoformat(),
                            "data": event.data,
                        }
                    )

                return EvaluationRun(
                    run_id=db_run.run_id,
                    timestamp=db_run.timestamp,
                    total_documents=db_run.total_documents,
                    completed_documents=db_run.completed_documents,
                    overall_accuracy=db_run.overall_accuracy,
                    execution_time=db_run.execution_time,
                    status=db_run.status,
                    documents=documents,
                    events=events,
                    name=db_run.name,
                    has_ground_truth=db_run.has_ground_truth,
                    model_name=db_run.model_name,
                )
            except Exception as e:
                logger.error(f"Failed to retrieve run {run_id}: {e}")
                return None

    def list_runs(self, limit: int = PaginationConfig.DEFAULT_LIMIT) -> list[dict[str, Any]]:
        """List recent evaluation runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of run summaries (without full document details)
        """
        with self.session_maker() as session:
            try:
                stmt = select(DBRun).order_by(DBRun.timestamp.desc()).limit(limit)
                runs = session.scalars(stmt).all()

                result = []
                for run in runs:
                    run_data = {
                        "run_id": run.run_id,
                        "name": run.name,
                        "timestamp": run.timestamp.isoformat(),
                        "total_documents": run.total_documents,
                        "completed_documents": run.completed_documents,
                        "execution_time": run.execution_time,
                        "status": run.status,
                        "has_ground_truth": run.has_ground_truth,
                        "model_name": run.model_name,
                    }
                    if run.has_ground_truth:
                        run_data["overall_accuracy"] = run.overall_accuracy
                    result.append(run_data)

                return result
            except Exception as e:
                logger.error(f"Failed to list runs: {e}")
                return []

    def update_run_model(self, run_id: RunID, model_name: str) -> bool:
        """Update the model name for a run.

        Args:
            run_id: Run identifier
            model_name: LiteLLM model identifier

        Returns:
            True if update succeeded, False otherwise
        """
        with self.session_maker() as session:
            try:
                db_run = session.query(DBRun).filter(DBRun.run_id == run_id).first()
                if db_run:
                    db_run.model_name = model_name
                    session.commit()
                    logger.info(f"Updated model_name for run {run_id} to {model_name}")
                    return True
                else:
                    logger.warning(f"Run {run_id} not found for model update")
                    return False
            except Exception as e:
                logger.error(f"Failed to update model for run {run_id}: {e}")
                session.rollback()
                return False

    def update_run_name(self, run_id: RunID, name: str) -> bool:
        """Update the display name of a run.

        Args:
            run_id: Run identifier
            name: New display name

        Returns:
            True if successful, False otherwise
        """
        with self.session_maker() as session:
            try:
                stmt = select(DBRun).where(DBRun.run_id == run_id)
                db_run = session.scalars(stmt).first()
                if not db_run:
                    logger.warning(f"Run {run_id} not found for name update")
                    return False

                db_run.name = name
                session.commit()
                logger.info(f"Updated run {run_id} name to '{name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to update run name for {run_id}: {e}")
                session.rollback()
                return False

    def save_event(
        self,
        run_id: RunID,
        event_type: EventType,
        document_id: DocumentID | None,
        data: dict[str, Any],
    ) -> None:
        """Save an event to the database.

        Args:
            run_id: Run identifier
            event_type: Type of event (use EventType enum)
            document_id: Optional document identifier
            data: Event data dictionary
        """
        with self.session_maker() as session:
            try:
                # Look up the Run record to get the integer ID
                stmt = select(DBRun).where(DBRun.run_id == run_id)
                db_run = session.scalars(stmt).first()
                if not db_run:
                    logger.warning(f"Run {run_id} not found for event save")
                    return

                db_event = DBRunEvent(
                    run_id=db_run.id,  # Use the integer ID
                    event_type=event_type,
                    document_id=document_id,
                    timestamp=datetime.now(UTC),
                    data=data,
                )
                session.add(db_event)
                session.commit()
                logger.debug(f"Saved event {event_type} for run {run_id}")
            except Exception as e:
                logger.error(f"Failed to save event {event_type} for run {run_id}: {e}")
                session.rollback()
