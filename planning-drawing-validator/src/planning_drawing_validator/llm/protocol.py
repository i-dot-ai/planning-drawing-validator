from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from planning_drawing_validator.models import CarbonImpact

__all__ = ["LLMProtocol"]


@runtime_checkable
class LLMProtocol(Protocol):
    """Protocol defining the interface for LLM client implementations.

    This is a lightweight structural protocol - implementations don't need to explicitly
    inherit from this class, they just need to implement the required methods.
    """

    async def generate_structured_output(
        self,
        parts: list[Any],
        schema: type[BaseModel],
        trace_name: str | None = None,
        reasoning_effort: str | None = None,
        convert_pdf_to_images: bool = False,
    ) -> tuple[dict[str, Any], CarbonImpact | None, str | None]:
        """Generate structured output from LLM using Pydantic models.

        Args:
            parts: List of content parts (text, images, PDFs) for the LLM.
                Format varies by provider but should support multimodal inputs.
            schema: Pydantic BaseModel class defining the expected response structure.
            trace_name: Optional name for tracing/observability (e.g., Langfuse).
            reasoning_effort: Optional reasoning/thinking effort level. Model-agnostic
                parameter supported by LiteLLM across providers.
                Values: "none" (disabled), "low", "medium", "high".
                If None, uses provider defaults.
            convert_pdf_to_images: Whether to convert PDFs to images before sending to LLM.
                Required for Azure-hosted OpenAI models which don't support 'file' content type.

        Returns:
            Tuple of (parsed JSON response as dictionary, carbon impact data, reasoning content).
            Carbon impact is None if not available from provider.
            Reasoning content is None if not enabled or not available.

        Raises:
            ValueError: If response is invalid or cannot be parsed.
            RuntimeError: If LLM API call fails.

        Note:
            Implementations should handle provider-specific error types and
            convert them to standard ValueError/RuntimeError exceptions.
        """
        ...

    async def generate_text(
        self,
        prompt: str,
        run_id: str | None = None,
    ) -> str:
        """Generate plain text output from LLM.

        Simple text generation for tasks like summarisation or rephrasing.

        Args:
            prompt: The text prompt to send to the LLM.
            run_id: Optional run ID for tracing.

        Returns:
            Generated text response.

        Raises:
            RuntimeError: If LLM API call fails.
        """
        ...
