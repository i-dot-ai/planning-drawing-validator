from dataclasses import dataclass, field
from typing import Any

from planning_drawing_validator.models import CarbonImpact, Document, ValidationResult

__all__ = [
    "GroundTruthDocument",
    "ComparisonResult",
    "EvaluationReport",
    "EvaluationResult",
]


@dataclass(slots=True)
class GroundTruthDocument:
    """Test document with known expected validation result.

    Used for quality assurance testing - combines a document with its
    expected validation outcome for performance measurement.

    Attributes:
        document: The document to validate.
        expected_validity: Expected validity assessment (VALID, INVALID, etc.).
        expected_reasoning: Optional expected reasoning (for detailed comparison).
    """

    document: Document
    expected_validity: str
    expected_reasoning: str | None = None


@dataclass(slots=True)
class ComparisonResult:
    """Comparison of predicted vs expected result for a single document.

    Attributes:
        document_id: Unique identifier for the document.
        predicted: The validation result from the production validator.
        expected_validity: The expected validity from ground truth.
        correct: Whether the prediction matches the expected result.
        expected_reasoning: Optional expected reasoning from ground truth.
    """

    document_id: str
    predicted: ValidationResult
    expected_validity: str
    correct: bool | None
    expected_reasoning: str | None = None


@dataclass(slots=True)
class ConfusionMatrix:
    """Confusion matrix for classification performance.

    Attributes:
        true_positives: Documents correctly classified as VALID.
        true_negatives: Documents correctly classified as INVALID.
        false_positives: Documents incorrectly classified as VALID.
        false_negatives: Documents incorrectly classified as INVALID.
    """

    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        """Calculate precision: TP / (TP + FP)."""
        denominator = self.true_positives + self.false_positives
        return self.true_positives / denominator if denominator > 0 else 0.0

    @property
    def recall(self) -> float:
        """Calculate recall: TP / (TP + FN)."""
        denominator = self.true_positives + self.false_negatives
        return self.true_positives / denominator if denominator > 0 else 0.0

    @property
    def f1_score(self) -> float:
        """Calculate F1 score: 2 * (precision * recall) / (precision + recall)."""
        denominator = self.precision + self.recall
        return 2 * (self.precision * self.recall) / denominator if denominator > 0 else 0.0


@dataclass(slots=True)
class EvaluationReport:
    """Aggregate performance metrics across a test dataset.

    Contains overall accuracy metrics and per-document comparison results.

    Attributes:
        total: Total number of documents evaluated.
        correct: Number of correct predictions.
        errors: Number of documents that failed to process (ERROR status).
        processed: Number of documents successfully processed (total - errors).
        accuracy: Accuracy over processed documents only (correct / processed).
        results: Per-document comparison results.
        confusion_matrix: Confusion matrix for detailed metrics (excludes errors).
        average_execution_time: Average time per document validation.
    """

    total: int
    correct: int
    errors: int
    processed: int
    accuracy: float
    results: list[ComparisonResult] = field(default_factory=list)
    confusion_matrix: ConfusionMatrix = field(default_factory=ConfusionMatrix)
    average_execution_time: float = 0.0

    @property
    def precision(self) -> float:
        """Get precision from confusion matrix."""
        return self.confusion_matrix.precision

    @property
    def recall(self) -> float:
        """Get recall from confusion matrix."""
        return self.confusion_matrix.recall

    @property
    def f1_score(self) -> float:
        """Get F1 score from confusion matrix."""
        return self.confusion_matrix.f1_score

    @property
    def error_rate(self) -> float:
        """Get error rate (errors / total)."""
        return self.errors / self.total if self.total > 0 else 0.0


def create_evaluation_report(
    results: list[ComparisonResult],
) -> EvaluationReport:
    """Create evaluation report from comparison results.

    Calculates aggregate metrics including accuracy and confusion matrix.
    ERRORs are counted separately and excluded from accuracy calculation.

    Args:
        results: List of per-document comparison results.

    Returns:
        Evaluation report with calculated metrics.
    """
    total = len(results)

    # Count errors (documents that failed to process)
    errors = sum(1 for r in results if r.predicted.validity == "ERROR")
    processed = total - errors

    # Count correct predictions (only from successfully processed documents)
    correct = sum(1 for r in results if r.correct is True)

    # Accuracy is calculated over processed documents only (excludes errors)
    accuracy = correct / processed if processed > 0 else 0.0

    # Build confusion matrix (skip errors and documents without ground truth)
    confusion = ConfusionMatrix()
    for result in results:
        # Skip documents with UNKNOWN expected validity (no ground truth)
        if result.expected_validity == "UNKNOWN":
            continue

        # Skip ERROR results - they shouldn't affect confusion matrix
        if result.predicted.validity == "ERROR":
            continue

        predicted_valid = result.predicted.validity == "VALID"
        expected_valid = result.expected_validity == "VALID"

        if predicted_valid and expected_valid:
            confusion.true_positives += 1
        elif not predicted_valid and not expected_valid:
            confusion.true_negatives += 1
        elif predicted_valid and not expected_valid:
            confusion.false_positives += 1
        else:  # not predicted_valid and expected_valid
            confusion.false_negatives += 1

    # Calculate average execution time
    avg_time = sum(r.predicted.execution_time for r in results) / total if total > 0 else 0.0

    return EvaluationReport(
        total=total,
        correct=correct,
        errors=errors,
        processed=processed,
        accuracy=accuracy,
        results=results,
        confusion_matrix=confusion,
        average_execution_time=avg_time,
    )


@dataclass(slots=True)
class EvaluationResult:
    """Result of evaluating a single document against ground truth.

    Used by the evaluation API to track per-document results including
    predictions, ground truth comparison, and execution metrics.

    Attributes:
        document_id: Unique identifier for the document.
        prompt_type: Type of prompt used for validation.
        ground_truth_validity: Expected validity from ground truth.
        ground_truth_reason: Expected reasoning from ground truth.
        predicted_validity: Predicted validity from validator.
        predicted_reasoning: Predicted reasoning from validator.
        confidence: Confidence level of prediction.
        correct: Whether prediction matches ground truth (None if no ground truth).
        requirements_checked: List of requirement check results.
        execution_time: Time taken for validation in seconds.
        success: Whether validation completed successfully.
        error_message: Error message if validation failed.
        document_type: Type of document (SITE_PLAN, FLOOR_PLAN, etc.).
        carbon_impact: Carbon and environmental impact metrics from LLM inference.
        reasoning_match_score: Score (0-1) indicating how well reasoning matches ground truth.
        reasoning_evaluated: Whether reasoning evaluation was performed.
        reasoning_explanation: Brief explanation of reasoning match evaluation.
    """

    document_id: str
    prompt_type: str
    ground_truth_validity: str | None
    ground_truth_reason: str | None
    predicted_validity: str
    predicted_reasoning: str
    confidence: str
    correct: bool | None
    requirements_checked: list[dict[str, Any]]
    execution_time: float
    success: bool
    error_message: str | None
    document_type: str | None
    carbon_impact: CarbonImpact | None = None
    # Reasoning evaluation fields
    reasoning_match_score: float | None = None
    reasoning_evaluated: bool = False
    reasoning_explanation: str | None = None
