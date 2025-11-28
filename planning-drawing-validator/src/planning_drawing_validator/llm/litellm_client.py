import asyncio
import base64
import json
import logging
from pathlib import Path
from typing import Any, cast

import fitz  # pymupdf
from pydantic import BaseModel

from planning_drawing_validator.models import CarbonImpact

__all__ = ["LiteLLMClient"]

logger = logging.getLogger(__name__)


# MIME type mapping for document encoding
_MIME_TYPE_MAP = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
}

# Magic byte signatures for image type detection
_IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"II*\x00": "image/tiff",  # Little-endian TIFF
    b"MM\x00*": "image/tiff",  # Big-endian TIFF
    b"%PDF": "application/pdf",
}


def _detect_mime_type_from_bytes(content: bytes) -> str:
    """Detect MIME type from file content using magic bytes.

    Args:
        content: Raw file content bytes.

    Returns:
        Detected MIME type or "application/octet-stream" if unknown.
    """
    for signature, mime_type in _IMAGE_SIGNATURES.items():
        if content.startswith(signature):
            return mime_type
    return "application/octet-stream"


def _content_contains_pdf(parts: list[Any]) -> bool:
    """Check if any part in the content list is a PDF.

    Args:
        parts: List of content parts (str, Path, bytes).

    Returns:
        True if any part is a PDF, False otherwise.
    """
    for part in parts:
        if isinstance(part, Path):
            if part.suffix.lower() == ".pdf":
                return True
        elif isinstance(part, bytes | bytearray):
            mime_type = _detect_mime_type_from_bytes(bytes(part))
            if mime_type == "application/pdf":
                return True
    return False


def _convert_pdf_to_images(pdf_content: bytes, dpi: int = 150) -> list[bytes]:
    """Convert PDF pages to PNG images using PyMuPDF.

    Args:
        pdf_content: Raw PDF bytes.
        dpi: Resolution for rendering (default 150 for good quality/size balance).

    Returns:
        List of PNG image bytes, one per page.
    """
    images = []
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_content, filetype="pdf")

        # Calculate zoom factor from DPI (72 is the base PDF DPI)
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page to pixmap (image)
            pixmap = page.get_pixmap(matrix=matrix)
            # Convert to PNG bytes
            png_bytes = pixmap.tobytes("png")
            images.append(png_bytes)
            logger.debug(
                f"Converted PDF page {page_num + 1}/{len(doc)} to PNG ({len(png_bytes)} bytes)"
            )

        doc.close()
        logger.info(f"Converted PDF to {len(images)} PNG images at {dpi} DPI")
    except Exception as e:
        logger.error(f"Failed to convert PDF to images: {e}")
        raise

    return images


class LiteLLMClient:
    """LLM client using i-dot-ai-utilities LiteLLMHandler.

    Uses i-dot-ai-utilities for all LiteLLM interactions with structured
    Pydantic outputs. The handler manages all LiteLLM configuration including
    optional Langfuse tracing.

    Configuration via environment variables:
        - IAI_LITELLM_PROJECT_NAME: Project name for Langfuse tracing
        - IAI_LITELLM_API_BASE: API base URL for your LiteLLM gateway
        - IAI_LITELLM_API_KEY: API key for authentication
        - IAI_LITELLM_CHAT_MODEL: Model name with openai/ prefix (e.g., openai/gemini-2.5-flash)
        - IAI_LITELLM_LANGFUSE_PUBLIC_KEY: Optional Langfuse public key
        - IAI_LITELLM_LANGFUSE_SECRET_KEY: Optional Langfuse secret key
        - IAI_LITELLM_LANGFUSE_HOST: Optional Langfuse host URL
    """

    def __init__(self, model_name: str | None = None) -> None:
        """Initialise LiteLLM client with i-dot-ai-utilities handler.

        Args:
            model_name: Optional model name override. If provided, overrides
                       IAI_LITELLM_CHAT_MODEL environment variable for this client instance.
                       Useful for testing different models or dynamic model selection.
        """
        try:
            from i_dot_ai_utilities.litellm.main import LiteLLMHandler
            from i_dot_ai_utilities.litellm.settings import Settings
            from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
        except ImportError as e:
            raise ImportError(
                "i-dot-ai-utilities package required. Install with: "
                "uv add 'i-dot-ai-utilities[litellm]'"
            ) from e

        logger.info(
            "LiteLLMHandler created - ecologits carbon tracking enabled via i-dot-ai-utilities"
        )

        # Load configuration and create handler
        settings = Settings()
        structured_logger = StructuredLogger(level=logging.INFO)
        self._handler = LiteLLMHandler(logger=structured_logger)

        # Override model if provided, otherwise use environment configuration
        if model_name:
            self._handler.chat_model = model_name

        logger.info(
            f"LiteLLM client initialised via i-dot-ai-utilities: model={self._handler.chat_model}, "
            f"api_base={settings.api_base}" + (" (overridden)" if model_name else "")
        )

    def _encode_document(
        self, source: Path | bytes | bytearray, convert_pdf_to_images: bool = False
    ) -> list[dict[str, Any]]:
        """Encode document to LiteLLM-compatible format.

        Uses OpenAI-style formats which LiteLLM translates for all providers:
        - Images: {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        - PDFs: {"type": "file", "file": {"filename": "...", "file_data": "data:application/pdf;base64,..."}}
          OR converted to images if convert_pdf_to_images=True

        Args:
            source: Path to document file, raw bytes, or bytearray.
            convert_pdf_to_images: If True, convert PDFs to PNG images. Required for
                Azure-hosted OpenAI models which don't support 'file' content type.

        Returns:
            List of formatted dicts for LiteLLM. Usually single-item, but multi-page PDFs
            converted to images return multiple items.

        Raises:
            FileNotFoundError: If file doesn't exist or is not a file.
            TypeError: If source type is not supported.
        """
        # Handle Path objects
        if isinstance(source, Path):
            if not source.exists() or not source.is_file():
                raise FileNotFoundError(f"Not a file: {source}")
            content = source.read_bytes()
            suffix = source.suffix.lower()
            mime_type = _MIME_TYPE_MAP.get(suffix, "application/pdf")
            filename = source.name
        # Handle bytes
        elif isinstance(source, bytes | bytearray):
            content = bytes(source)
            # Detect MIME type from magic bytes instead of assuming PDF
            mime_type = _detect_mime_type_from_bytes(content)
            logger.debug(f"Detected MIME type from bytes: {mime_type}")
            # Generate filename based on detected type
            ext = ".pdf" if mime_type == "application/pdf" else ".bin"
            filename = f"document{ext}"
        else:
            raise TypeError(f"Unsupported document source type: {type(source)}")

        # Handle PDF conversion to images if requested
        if mime_type == "application/pdf" and convert_pdf_to_images:
            logger.info(f"Converting PDF to images for Azure compatibility (filename={filename})")
            try:
                png_images = _convert_pdf_to_images(content)
                result = []
                for i, png_bytes in enumerate(png_images):
                    encoded_data = base64.b64encode(png_bytes).decode("utf-8")
                    result.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{encoded_data}"},
                        }
                    )
                logger.info(f"PDF converted to {len(result)} image(s)")
                return result
            except Exception as e:
                logger.warning(f"PDF-to-image conversion failed, falling back to file type: {e}")
                # Fall through to standard PDF encoding

        encoded_data = base64.b64encode(content).decode("utf-8")

        if mime_type.startswith("image/"):
            # Images: Use OpenAI image_url format - LiteLLM translates for all providers
            logger.debug(f"Encoding image as image_url (mime_type={mime_type})")
            return [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{encoded_data}"},
                }
            ]
        elif mime_type == "application/pdf":
            # PDFs: Use LiteLLM's file format with filename for OpenAI compatibility
            logger.debug(f"Encoding PDF as file type (filename={filename})")
            return [
                {
                    "type": "file",
                    "file": {
                        "filename": filename,
                        "file_data": f"data:{mime_type};base64,{encoded_data}",
                    },
                }
            ]
        else:
            return [{"type": "text", "text": f"[Document: {mime_type}]"}]

    def _convert_parts_to_messages(
        self, parts: list[Any], convert_pdf_to_images: bool = False
    ) -> list[dict[str, Any]]:
        """Convert parts format to LiteLLM messages format.

        Supports direct input formats only (no intermediate representations):
        - Strings: Plain text content
        - Path objects: Direct document encoding
        - bytes/bytearray: Direct document encoding

        Args:
            parts: List of content parts (str, Path, bytes only).
            convert_pdf_to_images: If True, convert PDFs to PNG images. Required for
                Azure-hosted OpenAI models which don't support 'file' content type.

        Returns:
            List of message dictionaries in OpenAI format.

        Raises:
            TypeError: If an unsupported part type is provided.
        """
        content_items: list[dict[str, Any]] = []

        for part in parts:
            if isinstance(part, str):
                content_items.append({"type": "text", "text": part})
            elif isinstance(part, Path | bytes | bytearray):
                # Direct document encoding - returns list (may be multiple for multi-page PDFs)
                content_items.extend(self._encode_document(part, convert_pdf_to_images))
            else:
                raise TypeError(
                    f"Unsupported part type: {type(part)}. "
                    f"Only str, Path, bytes, and bytearray are supported. "
                    f"Pass documents directly as Path or bytes instead of using intermediate formats."
                )

        return [{"role": "user", "content": content_items}]

    def _extract_carbon_impact(self, response: Any) -> CarbonImpact | None:
        """Extract carbon impact data from LLM response.

        Args:
            response: LLM response object from i-dot-ai-utilities handler

        Returns:
            CarbonImpact instance if impacts data is available, None otherwise
        """
        if not hasattr(response, "impacts"):
            logger.debug("Response does not have impacts attribute")
            return None

        try:
            impacts = response.impacts

            # Extract min/max from ecologits RangeValue objects
            # RangeValue has .min and .max attributes (not strings to split)
            energy_min = float(impacts.energy.value.min)
            energy_max = float(impacts.energy.value.max)
            gwp_min = float(impacts.gwp.value.min)
            gwp_max = float(impacts.gwp.value.max)
            adpe_min = float(impacts.adpe.value.min)
            adpe_max = float(impacts.adpe.value.max)
            pe_min = float(impacts.pe.value.min)
            pe_max = float(impacts.pe.value.max)
            wcf_min = float(impacts.wcf.value.min)
            wcf_max = float(impacts.wcf.value.max)

            carbon_impact = CarbonImpact(
                energy_kwh_min=energy_min,
                energy_kwh_max=energy_max,
                gwp_kgco2eq_min=gwp_min,
                gwp_kgco2eq_max=gwp_max,
                adpe_kgsbeq_min=adpe_min,
                adpe_kgsbeq_max=adpe_max,
                pe_mj_min=pe_min,
                pe_mj_max=pe_max,
                wcf_l_min=wcf_min,
                wcf_l_max=wcf_max,
            )

            logger.debug(
                f"Extracted carbon impact: {gwp_min:.6f}-{gwp_max:.6f} kgCO2eq, "
                f"{energy_min:.6f}-{energy_max:.6f} kWh, {wcf_min:.6f}-{wcf_max:.6f} L"
            )

            return carbon_impact

        except Exception as e:
            logger.error(f"Failed to extract carbon impact: {e}", exc_info=True)
            return None

    async def generate_structured_output(
        self,
        parts: list[Any],
        schema: type[BaseModel],
        trace_name: str | None = None,
        reasoning_effort: str | None = None,
        convert_pdf_to_images: bool = False,
        max_retries: int = 3,
    ) -> tuple[dict[str, Any], CarbonImpact | None, str | None]:
        """Generate structured output from LLM using Pydantic models.

        Args:
            parts: List of content parts (text, images, PDFs).
            schema: Pydantic BaseModel class defining the expected response structure.
            trace_name: Optional name for Langfuse trace. Currently unused as tracing is
                       configured globally via i-dot-ai-utilities environment variables
                       (IAI_LITELLM_LANGFUSE_*). Kept for LLMProtocol interface compatibility.
            reasoning_effort: Optional reasoning/thinking effort level. Model-agnostic parameter
                supported by LiteLLM across providers (Anthropic, Gemini, Deepseek, etc.).
                Values: "none" (disabled), "low", "medium", "high".
                If None, uses provider defaults (no reasoning parameter sent).
            convert_pdf_to_images: Whether to convert PDFs to images before sending to LLM.
                Required for Azure-hosted OpenAI models which don't support 'file' content type
                in the Chat Completions API.
            max_retries: Maximum number of retry attempts for transient failures (default: 3).

        Returns:
            Tuple of (parsed JSON response, carbon impact data, thinking/reasoning content).
            Carbon impact is None if not available.
            Reasoning content is None if not available or reasoning not enabled.

        Raises:
            ValueError: If response is invalid or cannot be parsed after all retries.
            RuntimeError: If LLM API call fails after all retries.
        """
        messages = self._convert_parts_to_messages(parts, convert_pdf_to_images)
        last_error: Exception | None = None
        response_text: str | None = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff: 1s, 2s, 4s...
                    wait_time = 2 ** (attempt - 1)
                    logger.info(
                        f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s wait"
                    )
                    await asyncio.sleep(wait_time)

                # Use i-dot-ai-utilities handler with Pydantic structured output
                # Note: chat_completion is synchronous, so we run it in thread pool
                logger.debug(f"Calling LiteLLMHandler with Pydantic model: {schema.__name__}")

                model_to_use = self._handler.chat_model

                # Build call parameters for chat completion
                call_params = {
                    "messages": messages,
                    "model": model_to_use,
                    "response_format": schema,
                }

                # Add reasoning_effort if specified - LiteLLM handles translation for each provider
                if reasoning_effort:
                    call_params["reasoning_effort"] = reasoning_effort
                    logger.debug(
                        f"Reasoning enabled: effort={reasoning_effort}, model={model_to_use}"
                    )

                response = await asyncio.to_thread(
                    self._handler.chat_completion,
                    **call_params,
                )

                # Extract thinking content if present (Gemini extended thinking)
                thinking_content = None
                message = response.choices[0].message

                # Check LiteLLM's reasoning_content field (standard for thinking/reasoning)
                if hasattr(message, "reasoning_content") and message.reasoning_content:
                    thinking_content = str(message.reasoning_content)
                    logger.debug(f"Extracted thinking content ({len(thinking_content)} chars)")

                # Alternative: Check thinking_blocks field
                elif hasattr(message, "thinking_blocks") and message.thinking_blocks:
                    if isinstance(message.thinking_blocks, list):
                        thinking_content = "\n\n".join(
                            str(block) for block in message.thinking_blocks
                        )
                    else:
                        thinking_content = str(message.thinking_blocks)
                    logger.debug(
                        f"Extracted thinking from thinking_blocks ({len(thinking_content)} chars)"
                    )

                response_text = response.choices[0].message.content
                if not response_text or not response_text.strip():
                    raise ValueError("Empty or whitespace-only response from LLM")

                # Strip whitespace and handle potential markdown code blocks
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

                logger.debug(f"LLM response (first 500 chars): {response_text[:500]}")

                parsed = json.loads(response_text)
                logger.debug(f"Parsed keys: {list(parsed.keys())}")

                # Log usage if available
                if hasattr(response, "usage") and response.usage:
                    usage = response.usage
                    logger.info(
                        f"LLM usage: input={usage.prompt_tokens}, "
                        f"output={usage.completion_tokens}, total={usage.total_tokens}"
                    )

                # Extract carbon impact from response
                carbon_impact = self._extract_carbon_impact(response)

                return parsed, carbon_impact, thinking_content

            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt == max_retries - 1:
                    error_msg = (
                        f"Failed to parse LLM JSON response after {max_retries} attempts: {e}"
                    )
                    logger.error(error_msg)
                    if response_text:
                        logger.debug(f"Last response: {response_text[:1000]}")
                    raise ValueError(error_msg) from e
                # Continue to next retry attempt

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}: {e}"
                )
                if attempt == max_retries - 1:
                    error_msg = f"LLM API call failed after {max_retries} attempts ({type(e).__name__}): {e}"
                    logger.error(error_msg, exc_info=True)
                    raise RuntimeError(error_msg) from e
                # Continue to next retry attempt

        # Should not reach here, but just in case
        raise RuntimeError(f"Unexpected retry loop exit. Last error: {last_error}")

    def get_available_models(self) -> list[str]:
        """Get list of available models from i-dot-ai-utilities handler.

        Returns:
            List of all model names supported by LiteLLM (not gateway-specific).

        Note:
            This returns all models LiteLLM supports, not just models available
            on your specific gateway. Use for reference only.
        """
        try:
            model_list = self._handler.get_all_models()
            logger.info(f"Retrieved {len(model_list)} LiteLLM-supported models")
            return cast(list[str], model_list)
        except Exception as e:
            error_msg = f"Failed to get model list: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e

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
        try:
            messages = [{"role": "user", "content": prompt}]

            # Use i-dot-ai-utilities handler (synchronous, run in thread pool)
            response = await asyncio.to_thread(
                self._handler.chat_completion,
                messages=messages,
                model=self._handler.chat_model,
            )

            response_text = response.choices[0].message.content
            if not response_text:
                raise RuntimeError("Empty response from LLM")

            return response_text.strip()

        except Exception as e:
            error_msg = f"LLM text generation failed: {type(e).__name__}: {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
