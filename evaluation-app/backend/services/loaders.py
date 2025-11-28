import io
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from planning_drawing_validator.models import Document

from backend.models import GroundTruthDocument

__all__ = [
    "load_ground_truth_dataset",
    "scan_documents_for_testing",
    "load_from_json",
    "load_from_yaml",
    "load_from_excel",
]

logger = logging.getLogger(__name__)


# Type alias for column configuration
ColumnConfigDict = dict[str, str | None]  # keys: filename, validity, reason


def load_ground_truth_dataset(
    data_dir: Path | None = None,
    ground_truth_path: str | Path | None = None,
    storage_prefix: str | None = None,
    column_config: ColumnConfigDict | None = None,
) -> list[GroundTruthDocument]:
    """Load ground truth test dataset from various sources and formats.

    Supports loading from:
    - Local filesystem (JSON, YAML, Excel)
    - S3 storage (JSON, YAML, Excel)
    - Auto-detection of ground truth files
    - Explicit file paths

    This is for EVALUATION purposes only - loading test datasets with
    expected validation results to measure performance.

    Args:
        data_dir: Local directory containing test documents and ground truth.
        ground_truth_path: Specific path to ground truth file (JSON/YAML/Excel).
        storage_prefix: S3 prefix for S3-stored test datasets.
        column_config: Optional dict with custom column names:
            - filename: Column name for document filename
            - validity: Column name for validity label
            - reason: Column name for reasoning/explanation

    Returns:
        List of GroundTruthDocument instances with documents and expected results.

    Raises:
        ValueError: If neither data_dir nor storage_prefix provided.
        FileNotFoundError: If specified ground truth file not found.

    Example:
        # Load from explicit file
        dataset = load_ground_truth_dataset(
            data_dir=Path("test_data"),
            ground_truth_path="ground_truth.yaml"
        )

        # Auto-detect ground truth file
        dataset = load_ground_truth_dataset(data_dir=Path("test_data"))

        # Load from S3
        dataset = load_ground_truth_dataset(storage_prefix="test_runs/run_123/")
    """
    logger.info(
        f"Loading ground truth dataset: data_dir={data_dir}, "
        f"ground_truth_path={ground_truth_path}, storage_prefix={storage_prefix}, "
        f"column_config={column_config}"
    )

    # S3 storage path
    if storage_prefix:
        return _load_from_storage(storage_prefix, ground_truth_path, column_config)

    # Local filesystem path
    if not data_dir:
        raise ValueError("Either data_dir or storage_prefix must be provided")

    return _load_from_local(data_dir, ground_truth_path, column_config)


def scan_documents_for_testing(
    data_dir: Path | None = None,
    storage_prefix: str | None = None,
) -> list[GroundTruthDocument]:
    """Scan directory or S3 for documents without ground truth labels.

    Creates GroundTruthDocument instances with expected_validity="UNKNOWN"
    for documents that don't have ground truth labels. Useful for:
    - Testing validation on new unlabelled documents
    - Preparing datasets for labelling
    - Running production validation in evaluation mode

    Args:
        data_dir: Local directory to scan for documents.
        storage_prefix: S3 prefix to scan for documents.

    Returns:
        List of GroundTruthDocument instances with UNKNOWN expected results.

    Example:
        # Scan local directory for PDFs
        documents = scan_documents_for_testing(data_dir=Path("new_documents"))

        # Run validation without comparison
        validator = DocumentValidator()
        evaluator = PerformanceEvaluator(validator)
        # Will validate but can't calculate accuracy without expected results
    """
    logger.info(f"Scanning for test documents: data_dir={data_dir}, storage_prefix={storage_prefix}")

    # Supported document extensions
    document_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}

    # S3 scanning
    if storage_prefix:
        return _scan_storage_documents(storage_prefix, document_extensions)

    # Local filesystem scanning
    if not data_dir:
        raise ValueError("Either data_dir or storage_prefix must be provided")

    return _scan_local_documents(data_dir, document_extensions)


def load_from_json(file_path: Path) -> list[GroundTruthDocument]:
    """Load ground truth dataset from JSON file.

    Expected format:
    [
        {
            "document_id": "doc-001",
            "filename": "site-plan.pdf",
            "validity": "VALID",
            "reason": "Meets all requirements",
            "storage_key": "optional/s3/key.pdf"
        },
        ...
    ]

    Args:
        file_path: Path to JSON file.

    Returns:
        List of GroundTruthDocument instances.
    """
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    return _parse_ground_truth_records(data)


def load_from_yaml(file_path: Path) -> list[GroundTruthDocument]:
    """Load ground truth dataset from YAML file.

    Expected format:
    - document_id: doc-001
      filename: site-plan.pdf
      validity: VALID
      reason: Meets all requirements
      storage_key: optional/s3/key.pdf
    ...

    Args:
        file_path: Path to YAML file.

    Returns:
        List of GroundTruthDocument instances.
    """
    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return _parse_ground_truth_records(data)


def load_from_excel(
    file_path: Path,
    doc_column: str = "Document number",
    column_config: ColumnConfigDict | None = None,
) -> list[GroundTruthDocument]:
    """Load ground truth dataset from Excel file (legacy format).

    Expected columns:
    - "Document number" or "Document name": Document filename
    - "Valid/Invalid": Validity status
    - "Reason for invalidity": Optional reasoning (can be empty)

    Args:
        file_path: Path to Excel file.
        doc_column: Name of column containing document filenames (legacy, used as fallback).
        column_config: Optional custom column names (takes precedence over doc_column).

    Returns:
        List of GroundTruthDocument instances.
    """
    df = pd.read_excel(file_path)

    return _parse_excel_records(
        df,
        doc_column,
        filename_col=column_config.get("filename") if column_config else None,
        validity_col=column_config.get("validity") if column_config else None,
        reason_col=column_config.get("reason") if column_config else None,
    )


def _load_from_storage(
    storage_prefix: str,
    ground_truth_path: str | Path | None,
    column_config: ColumnConfigDict | None = None,
) -> list[GroundTruthDocument]:
    """Load ground truth from S3 storage.

    Args:
        storage_prefix: S3 prefix where test dataset is stored.
        ground_truth_path: Optional specific ground truth file within prefix.
        column_config: Optional custom column names for Excel files.

    Returns:
        List of GroundTruthDocument instances.
    """
    from backend.storage.client import get_storage_client

    storage = get_storage_client()

    # Load specific ground truth file
    if ground_truth_path:
        gt_filename = str(ground_truth_path).split("/")[-1]
        storage_key = f"{storage_prefix.rstrip('/')}/{gt_filename}"

        content = storage.get_object(storage_key)
        if not content:
            raise FileNotFoundError(f"Ground truth file not found in S3: {storage_key}")

        return _parse_storage_content(content, gt_filename, column_config)

    # Auto-detect ground truth files in S3 prefix
    objects = storage.list_objects(prefix=storage_prefix)

    # Try JSON/YAML first (preferred formats)
    for obj_key in objects:
        filename = obj_key.split("/")[-1]
        if filename in ["ground_truth.json", "ground_truth.yaml", "ground_truth.yml"]:
            content = storage.get_object(obj_key)
            if content:
                dataset = _parse_storage_content(content, filename, column_config)
                if dataset:
                    logger.info(f"Loaded {len(dataset)} test documents from {obj_key}")
                    return dataset

    # Fall back to Excel (legacy format)
    excel_files = [
        ("List of drawings 1.xlsx", "Document number"),
        ("List of drawings 2.xlsx", "Document name"),
    ]
    for excel_filename, doc_col in excel_files:
        for obj_key in objects:
            if obj_key.endswith(excel_filename):
                content = storage.get_object(obj_key)
                if content:
                    df = pd.read_excel(io.BytesIO(content))
                    dataset = _parse_excel_records(
                        df,
                        doc_col,
                        filename_col=column_config.get("filename") if column_config else None,
                        validity_col=column_config.get("validity") if column_config else None,
                        reason_col=column_config.get("reason") if column_config else None,
                    )
                    if dataset:
                        logger.info(f"Loaded {len(dataset)} test documents from {obj_key}")
                        return dataset

    # No ground truth files found - fall back to document scanning
    logger.warning(
        f"No ground truth files found in S3 prefix {storage_prefix}, "
        "falling back to document scan (UNKNOWN expected results)"
    )
    return _scan_storage_documents(storage_prefix, {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"})


def _parse_storage_content(
    content: bytes,
    filename: str,
    column_config: ColumnConfigDict | None = None,
) -> list[GroundTruthDocument]:
    """Parse ground truth content from S3 object.

    Args:
        content: File content as bytes.
        filename: Original filename (for format detection).
        column_config: Optional custom column names for Excel files.

    Returns:
        List of GroundTruthDocument instances.
    """
    if filename.endswith(".json"):
        data = json.loads(content.decode("utf-8"))
        return _parse_ground_truth_records(data)
    elif filename.endswith((".yaml", ".yml")):
        data = yaml.safe_load(io.BytesIO(content))
        return _parse_ground_truth_records(data)
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(content))
        # Auto-detect document column
        doc_col = "Document number" if "Document number" in df.columns else "Document name"
        return _parse_excel_records(
            df,
            doc_col,
            filename_col=column_config.get("filename") if column_config else None,
            validity_col=column_config.get("validity") if column_config else None,
            reason_col=column_config.get("reason") if column_config else None,
        )
    else:
        raise ValueError(f"Unsupported ground truth file format: {filename}")


def _scan_storage_documents(storage_prefix: str, document_extensions: set[str]) -> list[GroundTruthDocument]:
    """Scan S3 prefix for documents without ground truth.

    Args:
        storage_prefix: S3 prefix to scan.
        document_extensions: Set of valid document file extensions.

    Returns:
        List of GroundTruthDocument instances with UNKNOWN expected results.
    """
    from backend.database.connection import get_session_maker
    from backend.database.models import StoredFile
    from backend.storage.client import get_storage_client

    storage = get_storage_client()
    documents: list[GroundTruthDocument] = []
    seen = set()

    # Try to get files from run_metadata.json (single source of truth)
    try:
        metadata_key = f"{storage_prefix.rstrip('/')}/run_metadata.json"
        metadata_content = storage.get_object(metadata_key)
        if metadata_content:
            metadata = json.loads(metadata_content.decode("utf-8"))
            files = metadata.get("files", [])

            for file_info in files:
                filename = file_info.get("filename", "")
                if filename and filename not in seen:
                    seen.add(filename)
                    documents.append(
                        GroundTruthDocument(
                            document=Document(
                                document_id=filename,
                                filename=filename,
                            ),
                            expected_validity="UNKNOWN",
                        )
                    )
            # Enrich with storage_keys from database below
    except Exception as e:
        logger.warning(f"Failed to load run metadata: {e}")

    # Try to get files from database (for hash-based storage)
    try:
        Session = get_session_maker()
        with Session() as session:
            # Extract run_id from storage_prefix
            run_id = storage_prefix.rstrip("/").split("/")[-1]

            # Query database for files in this run
            stored_files = (
                session.query(StoredFile)
                .filter(
                    StoredFile.run_id == run_id,
                    StoredFile.file_category == "document",
                )
                .all()
            )

            if stored_files:
                # Create mapping of filename to storage_key
                filename_to_storage_key = {
                    stored_file.original_filename.split("/")[-1]: stored_file.storage_key
                    for stored_file in stored_files
                }

                # Enrich existing documents with storage_keys
                if documents:
                    for doc in documents:
                        if doc.document.filename in filename_to_storage_key:
                            # Create new Document with storage_key (dataclasses are immutable with slots)
                            doc.document = Document(
                                document_id=doc.document.document_id,
                                filename=doc.document.filename,
                                storage_key=filename_to_storage_key[doc.document.filename],
                            )
                    return sorted(documents, key=lambda x: x.document.filename)
                else:
                    # Create documents from database records
                    for stored_file in stored_files:
                        filename = stored_file.original_filename.split("/")[-1]
                        if filename not in seen:
                            seen.add(filename)
                            documents.append(
                                GroundTruthDocument(
                                    document=Document(
                                        document_id=filename,
                                        filename=filename,
                                        storage_key=stored_file.storage_key,
                                    ),
                                    expected_validity="UNKNOWN",
                                )
                            )
                    return sorted(documents, key=lambda x: x.document.filename)
    except Exception as e:
        logger.warning(f"Database lookup failed: {e}")

    # Fall back to S3 object listing
    objects = storage.list_objects(prefix=storage_prefix)

    for obj_key in objects:
        # Skip metadata files
        if obj_key.endswith(".run_metadata.json"):
            continue

        filename = obj_key.split("/")[-1]
        if not filename:
            continue

        # Check if file has supported extension
        file_ext = Path(filename).suffix.lower()
        if file_ext in document_extensions:
            if filename not in seen:
                seen.add(filename)
                documents.append(
                    GroundTruthDocument(
                        document=Document(
                            document_id=filename,
                            filename=filename,
                        ),
                        expected_validity="UNKNOWN",
                    )
                )

    return sorted(documents, key=lambda x: x.document.filename)


def _load_from_local(
    data_dir: Path,
    ground_truth_path: str | Path | None,
    column_config: ColumnConfigDict | None = None,
) -> list[GroundTruthDocument]:
    """Load ground truth from local filesystem.

    Args:
        data_dir: Directory containing test documents and ground truth.
        ground_truth_path: Optional specific ground truth file path.
        column_config: Optional custom column names for Excel files.

    Returns:
        List of GroundTruthDocument instances.
    """
    # Load from specific file
    if ground_truth_path:
        gt_path = Path(ground_truth_path)

        # Handle relative paths (relative to data_dir)
        if not gt_path.is_absolute():
            gt_path = data_dir / gt_path

        if not gt_path.exists():
            raise FileNotFoundError(f"Ground truth file not found: {gt_path}")

        # Load based on file extension
        if gt_path.suffix == ".json":
            return load_from_json(gt_path)
        elif gt_path.suffix in [".yaml", ".yml"]:
            return load_from_yaml(gt_path)
        elif gt_path.suffix == ".xlsx":
            return load_from_excel(gt_path, column_config=column_config)
        else:
            raise ValueError(f"Unsupported ground truth file format: {gt_path.suffix}")

    # Auto-detect ground truth files
    # Try JSON/YAML first (preferred formats)
    for filename in ["ground_truth.json", "ground_truth.yaml", "ground_truth.yml"]:
        gt_path = data_dir / filename
        if gt_path.exists():
            if filename.endswith(".json"):
                dataset = load_from_json(gt_path)
            else:
                dataset = load_from_yaml(gt_path)

            if dataset:
                logger.info(f"Loaded {len(dataset)} test documents from {gt_path}")
                return dataset

    # Fall back to Excel (legacy format)
    excel_files = [
        ("List of drawings 1.xlsx", "Document number"),
        ("List of drawings 2.xlsx", "Document name"),
    ]
    for filename, doc_col in excel_files:
        excel_path = data_dir / filename
        if excel_path.exists():
            dataset = load_from_excel(excel_path, doc_col)
            if dataset:
                logger.info(f"Loaded {len(dataset)} test documents from {excel_path}")
                return dataset

    # No ground truth files found
    logger.warning(f"No ground truth files found in {data_dir}, returning empty dataset")
    return []


def _scan_local_documents(data_dir: Path, document_extensions: set[str]) -> list[GroundTruthDocument]:
    """Scan local directory for documents without ground truth.

    Args:
        data_dir: Directory to scan recursively.
        document_extensions: Set of valid document file extensions.

    Returns:
        List of GroundTruthDocument instances with UNKNOWN expected results.
    """
    documents: list[GroundTruthDocument] = []
    seen = set()

    # Scan directory recursively for documents
    for ext in document_extensions:
        for file_path in data_dir.rglob(f"*{ext}"):
            if file_path.is_file():
                filename = file_path.name
                if filename not in seen:
                    seen.add(filename)
                    documents.append(
                        GroundTruthDocument(
                            document=Document(
                                document_id=filename,
                                filename=filename,
                            ),
                            expected_validity="UNKNOWN",
                        )
                    )

    return sorted(documents, key=lambda x: x.document.filename)


def _parse_ground_truth_records(
    data: list[dict[str, Any]],
) -> list[GroundTruthDocument]:
    """Parse ground truth records from JSON/YAML data.

    Args:
        data: List of dictionaries with ground truth records.

    Returns:
        List of GroundTruthDocument instances.
    """
    print(f"🔍 JSON/YAML PARSING: {len(data)} records", flush=True)
    if data:
        print(f"🔍 SAMPLE RECORD KEYS: {list(data[0].keys())}", flush=True)
        print(f"🔍 SAMPLE RECORD: {data[0]}", flush=True)

    documents: list[GroundTruthDocument] = []
    seen = set()

    for entry in data:
        # Extract fields
        document_id = entry.get("document_id", entry.get("filename", ""))
        filename = entry.get("filename", "")
        validity = entry.get("validity", "")
        reason = entry.get("reason")
        storage_key = entry.get("storage_key")

        # Validate required fields
        if not filename or not validity or filename in seen:
            continue
        # Normalize validity - treat CLARIFICATION_NEEDED as UNKNOWN for evaluation purposes
        validity_upper = validity.upper()
        if validity_upper not in [
            "VALID",
            "INVALID",
            "UNKNOWN",
            "CLARIFICATION_NEEDED",
        ]:
            logger.warning(f"Skipping document with invalid validity: {validity}")
            continue
        # Map CLARIFICATION_NEEDED to UNKNOWN for evaluation (can't compare against it)
        if validity_upper == "CLARIFICATION_NEEDED":
            validity_upper = "UNKNOWN"
        else:
            validity_upper = validity.upper()

        seen.add(filename)

        # Create Document and GroundTruthDocument
        document = Document(
            document_id=document_id or filename,
            filename=filename,
            storage_key=storage_key,
        )

        if reason:
            print(f"🔍 RECORD WITH REASON: {filename} -> {repr(reason)[:80]}", flush=True)

        documents.append(
            GroundTruthDocument(
                document=document,
                expected_validity=validity_upper,
                expected_reasoning=reason,
            )
        )

    records_with_reason = sum(1 for d in documents if d.expected_reasoning)
    print(
        f"🔍 JSON/YAML RESULT: {len(documents)} docs, {records_with_reason} with reasoning",
        flush=True,
    )
    return sorted(documents, key=lambda x: x.document.filename)


def _find_column_case_insensitive(df: pd.DataFrame, target_names: list[str]) -> str | None:
    """Find a column name in DataFrame using case-insensitive matching.

    Args:
        df: Pandas DataFrame to search
        target_names: List of possible column names to match (in priority order)

    Returns:
        The actual column name if found, None otherwise
    """
    # Create a mapping of lowercase column names to actual column names
    col_map = {col.lower().strip(): col for col in df.columns}

    for target in target_names:
        normalized = target.lower().strip()
        if normalized in col_map:
            return col_map[normalized]
    return None


def _get_cell_value(row: pd.Series, col_name: str | None) -> Any:
    """Get cell value from row, handling None column name."""
    if col_name is None:
        return None
    val = row.get(col_name)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return val


def _parse_excel_records(
    df: pd.DataFrame,
    doc_column: str,
    filename_col: str | None = None,
    validity_col: str | None = None,
    reason_col: str | None = None,
) -> list[GroundTruthDocument]:
    """Parse ground truth records from Excel DataFrame.

    Args:
        df: Pandas DataFrame with ground truth data.
        doc_column: Name of column containing document filenames (legacy, used if filename_col not specified).
        filename_col: Custom column name for document filename.
        validity_col: Custom column name for validity label.
        reason_col: Custom column name for reasoning.

    Returns:
        List of GroundTruthDocument instances.
    """
    # Find columns using case-insensitive matching with fallbacks
    filename_column = _find_column_case_insensitive(
        df, [filename_col] if filename_col else []
    ) or _find_column_case_insensitive(df, [doc_column, "filename", "document", "file", "name"])

    validity_column = _find_column_case_insensitive(
        df, [validity_col] if validity_col else []
    ) or _find_column_case_insensitive(df, ["valid/invalid", "validity", "label", "status", "valid"])

    reason_column = _find_column_case_insensitive(
        df, [reason_col] if reason_col else []
    ) or _find_column_case_insensitive(df, ["reason for invalidity", "reason", "reasoning", "explanation", "notes"])

    print(f"🔍 EXCEL COLUMNS: {list(df.columns)}", flush=True)
    print(
        f"🔍 COLUMN MAPPING: filename={filename_column}, validity={validity_column}, reason={reason_column}",
        flush=True,
    )
    logger.info(f"Excel column mapping: filename={filename_column}, validity={validity_column}, reason={reason_column}")

    if not filename_column:
        logger.warning(f"Could not find filename column in DataFrame. Columns: {list(df.columns)}")
        return []

    if not validity_column:
        logger.warning(f"Could not find validity column in DataFrame. Columns: {list(df.columns)}")
        return []

    documents: list[GroundTruthDocument] = []
    seen = set()

    for _, row in df.iterrows():
        # Extract fields using resolved column names
        document_name = str(_get_cell_value(row, filename_column) or "")
        validity = str(_get_cell_value(row, validity_column) or "")
        reason = _get_cell_value(row, reason_column)

        # Extract just the filename (remove path)
        filename = document_name.split("/")[-1] if document_name else ""

        # Validate required fields
        if not filename or not validity or filename in seen:
            continue

        # Normalize validity - accept valid, invalid, and clarification_needed
        validity_lower = validity.lower().strip()
        if validity_lower not in [
            "valid",
            "invalid",
            "clarification_needed",
            "clarification needed",
            "unknown",
        ]:
            logger.warning(f"Skipping document with unrecognized validity: {validity}")
            continue

        # Map clarification_needed to UNKNOWN for evaluation purposes
        if validity_lower in ["clarification_needed", "clarification needed"]:
            validity_normalized = "UNKNOWN"
        else:
            validity_normalized = validity.upper()

        seen.add(filename)

        # Create Document and GroundTruthDocument
        document = Document(
            document_id=filename,
            filename=filename,
        )

        expected_reasoning = str(reason).strip() if reason and pd.notna(reason) else None
        if expected_reasoning:
            logger.info(
                f"Ground truth record with reasoning: filename={filename}, "
                f"expected_reasoning={repr(expected_reasoning)[:80]}"
            )

        documents.append(
            GroundTruthDocument(
                document=document,
                expected_validity=validity_normalized,
                expected_reasoning=expected_reasoning,
            )
        )

    # Log summary
    records_with_reasoning = [d for d in documents if d.expected_reasoning]
    logger.info(
        f"Parsed {len(documents)} ground truth records from Excel, "
        f"{len(records_with_reasoning)} have expected_reasoning"
    )
    return sorted(documents, key=lambda x: x.document.filename)
