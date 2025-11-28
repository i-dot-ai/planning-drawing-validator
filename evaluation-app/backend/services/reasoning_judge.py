"""Reasoning evaluation service using LLM-as-judge pattern.

This service compares the predicted reasoning from the validator against
the expected reasoning from ground truth to evaluate reasoning quality.
"""

import logging
from dataclasses import dataclass

from planning_drawing_validator.llm.factory import get_llm_client
from planning_drawing_validator.llm.protocol import LLMProtocol
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

__all__ = ["ReasoningJudge", "ReasoningEvaluation"]


class ReasoningJudgeResponse(BaseModel):
    """Structured response from the reasoning judge LLM."""

    match_score: float = Field(
        description="Score from 0.0 to 1.0 indicating how well the predicted reasoning matches the expected reasoning. "
        "1.0 = perfect semantic match, 0.0 = completely different reasoning."
    )
    key_points_matched: list[str] = Field(
        description="List of key points from the expected reasoning that were correctly identified in the predicted reasoning."
    )
    key_points_missed: list[str] = Field(
        description="List of key points from the expected reasoning that were NOT found in the predicted reasoning."
    )
    extra_points: list[str] = Field(
        description="List of additional points in the predicted reasoning not present in expected (may be valid observations)."
    )
    explanation: str = Field(
        description="Brief explanation of the match score, highlighting the main similarities and differences."
    )


@dataclass(slots=True)
class ReasoningEvaluation:
    """Result of evaluating reasoning quality.

    Attributes:
        match_score: Score from 0.0 to 1.0 indicating semantic match quality.
        key_points_matched: Points correctly identified.
        key_points_missed: Points missed from expected reasoning.
        extra_points: Additional observations in predicted reasoning.
        explanation: Brief explanation of the evaluation.
        evaluated: Whether evaluation was performed (False if no ground truth reasoning).
        error: Error message if evaluation failed.
    """

    match_score: float | None
    key_points_matched: list[str]
    key_points_missed: list[str]
    extra_points: list[str]
    explanation: str | None
    evaluated: bool
    error: str | None = None


REASONING_JUDGE_PROMPT = """You are an expert evaluator comparing two pieces of reasoning about a planning document's validity.

Your task is to evaluate how well the PREDICTED reasoning matches the EXPECTED reasoning semantically.
Focus on whether the key points and conclusions are the same, not on exact wording.

## Expected Reasoning (Ground Truth)
{expected_reasoning}

## Predicted Reasoning (From Model)
{predicted_reasoning}

## Evaluation Guidelines

1. **Semantic Match**: Focus on meaning, not exact wording. Different phrasing of the same point counts as a match.

2. **Key Points**: Identify the main reasons/issues mentioned in the expected reasoning and check if they appear in the predicted reasoning.

3. **Scoring**:
   - 1.0: All key points matched, conclusions align perfectly
   - 0.8-0.9: Most key points matched, minor details differ
   - 0.6-0.7: Core reasoning aligns but some important points missed
   - 0.4-0.5: Partial overlap, significant differences
   - 0.2-0.3: Minimal overlap, different focus
   - 0.0-0.1: Completely different reasoning

4. **Extra Points**: Note any valid observations in the predicted reasoning not mentioned in expected - these aren't necessarily wrong.

Evaluate the reasoning match and provide your assessment."""


class ReasoningJudge:
    """Service for evaluating reasoning quality using LLM-as-judge.

    Uses a separate LLM call to compare predicted vs expected reasoning
    and determine semantic similarity.
    """

    def __init__(
        self,
        model_name: str | None = None,
        llm_client: LLMProtocol | None = None,
    ):
        """Initialize the reasoning judge.

        Args:
            model_name: Optional LiteLLM model identifier for the judge.
                       If not specified, uses the default model.
            llm_client: Optional LLM client instance (for testing).
        """
        self.model_name = model_name
        self.llm_client = llm_client or get_llm_client(model_name)

    async def evaluate(
        self,
        expected_reasoning: str | None,
        predicted_reasoning: str | None,
        trace_name: str | None = None,
    ) -> ReasoningEvaluation:
        """Evaluate how well predicted reasoning matches expected reasoning.

        Args:
            expected_reasoning: The ground truth reasoning to compare against.
            predicted_reasoning: The model's predicted reasoning to evaluate.
            trace_name: Optional trace name for observability.

        Returns:
            ReasoningEvaluation with match score and analysis.
        """
        # Skip if no ground truth reasoning
        if not expected_reasoning or not expected_reasoning.strip():
            return ReasoningEvaluation(
                match_score=None,
                key_points_matched=[],
                key_points_missed=[],
                extra_points=[],
                explanation=None,
                evaluated=False,
            )

        # Skip if no predicted reasoning
        if not predicted_reasoning or not predicted_reasoning.strip():
            return ReasoningEvaluation(
                match_score=0.0,
                key_points_matched=[],
                key_points_missed=["All expected points - no reasoning provided"],
                extra_points=[],
                explanation="No predicted reasoning was provided to evaluate.",
                evaluated=True,
            )

        try:
            # Format the prompt
            prompt = REASONING_JUDGE_PROMPT.format(
                expected_reasoning=expected_reasoning.strip(),
                predicted_reasoning=predicted_reasoning.strip(),
            )

            # Call LLM with structured output
            result, _, _ = await self.llm_client.generate_structured_output(
                [prompt],
                ReasoningJudgeResponse,
                trace_name=f"{trace_name}_reasoning_judge" if trace_name else "reasoning_judge",
                reasoning_effort=None,  # Use default for judge - no extended thinking needed
            )

            response = ReasoningJudgeResponse.model_validate(result)

            return ReasoningEvaluation(
                match_score=max(0.0, min(1.0, response.match_score)),  # Clamp to [0, 1]
                key_points_matched=response.key_points_matched,
                key_points_missed=response.key_points_missed,
                extra_points=response.extra_points,
                explanation=response.explanation,
                evaluated=True,
            )

        except Exception as e:
            logger.error(f"Reasoning evaluation failed: {e}")
            return ReasoningEvaluation(
                match_score=None,
                key_points_matched=[],
                key_points_missed=[],
                extra_points=[],
                explanation=None,
                evaluated=False,
                error=str(e),
            )
