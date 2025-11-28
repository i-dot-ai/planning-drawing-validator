"""Utility functions for the demo validation API."""

import re
from typing import Any

from planning_drawing_validator.pipeline.schemas import (
    VALIDATION_CHECK_MODELS,
    DocumentType,
)


def normalise_document_type(value: str | None) -> str | None:
    """Normalise document type strings to match API schema format.

    Maps DocumentType enum values to the API schema's expected format:
    - section_drawing -> SECTION
    - mixed_plans -> MIXED
    - floor_plan -> FLOOR_PLAN
    - etc.

    Args:
        value: Raw document type string (from DocumentType enum or other source)

    Returns:
        Normalised type string matching API schema pattern, or None
    """
    if value is None:
        return None

    # Convert to uppercase and clean
    cleaned = str(value).upper().strip()

    # Strip enum prefixes (e.g., "DOCUMENTTYPE.SITE_PLAN" -> "SITE_PLAN")
    if "." in cleaned:
        cleaned = cleaned.split(".")[-1]

    # Normalise delimiters
    cleaned = cleaned.replace("-", "_")

    # Special case mappings for API schema compatibility
    mappings = {
        "MIXED_PLANS": "MIXED",
        "MIXED_PLAN": "MIXED",
        "SECTION_DRAWING": "SECTION",
        "SECTION_DRAWINGS": "SECTION",
    }

    if cleaned in mappings:
        return mappings[cleaned]

    # Remove redundant suffixes for other types
    for suffix in ("_DRAWING", "_DRAWINGS"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break

    # Handle plural forms (e.g., FLOOR_PLANS -> FLOOR_PLAN)
    if cleaned.endswith("S") and not cleaned.endswith("_PLANS"):
        potential_singular = cleaned[:-1]
        # Only remove S if it makes sense (avoid breaking CANVAS -> CANVA)
        if potential_singular.endswith("_PLAN"):
            cleaned = potential_singular

    return cleaned


def extract_scales_from_description(description: str) -> list[str]:
    """Extract typical scales from validation field description.

    Args:
        description: Field description text

    Returns:
        List of unique scale strings (e.g., ["1:50", "1:100"])
    """
    scales = re.findall(r"1:\d+", description)
    return list(dict.fromkeys(scales))  # Deduplicate while preserving order


def get_drawing_type_info(doc_type: DocumentType) -> dict[str, Any]:
    """Extract information about a drawing type from its validation model.

    Args:
        doc_type: Document type enum value

    Returns:
        Dictionary with type, display_name, typical_scales, and requirements
    """
    check_model = VALIDATION_CHECK_MODELS.get(doc_type.value)

    display_name = doc_type.value.replace("_", " ").title()

    if not check_model:
        return {
            "type": doc_type.value.upper(),
            "display_name": display_name,
            "typical_scales": [],
            "requirements": [],
        }

    requirements = []
    typical_scales = []

    for field_name, field_info in check_model.model_fields.items():
        if not field_info.description:
            continue

        desc = field_info.description

        # Extract scales from the scale field
        if field_name == "scale":
            typical_scales = extract_scales_from_description(desc)

        # Build requirement text from first sentence
        first_sentence = desc.split(".")[0].strip()

        # Mark critical requirements
        is_critical = field_info.json_schema_extra and field_info.json_schema_extra.get("critical", False)

        requirement_text = f"{first_sentence} (critical)" if is_critical else first_sentence
        requirements.append(requirement_text)

    return {
        "type": doc_type.value.upper(),
        "display_name": display_name,
        "typical_scales": typical_scales,
        "requirements": requirements,
    }
