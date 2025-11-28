import hashlib
import io
import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    get_app_state,
    get_db_session,
    get_storage,
)
from backend.api.error_handlers import bad_request, handle_error, internal_error
from backend.api.models.requests import (
    GroundTruthPathRequest,
    SaveGroundTruthRequest,
    UpdateDocumentGroundTruthRequest,
)
from backend.api.models.responses import (
    GroundTruthDataResponse,
    GroundTruthEntry,
    GroundTruthSaveResponse,
    GroundTruthUpdateResponse,
    GroundTruthUploadResponse,
)
from backend.database.models import Run as DBRun
from backend.services.loaders import load_ground_truth_dataset
from backend.services.run_metadata_service import update_run_metadata
from backend.state import AppState
from backend.storage.client import StorageClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ground-truth", tags=["ground_truth"])


@router.get("")
async def get_ground_truth(
    path: str,
    storage: StorageClient = Depends(get_storage),
) -> GroundTruthDataResponse:
    """Fetch ground truth data from S3 storage.

    Args:
        path: S3 path to the ground truth JSON file
        storage: Storage client dependency

    Returns:
        Ground truth data with entries

    Raises:
        HTTPException: If file not found or invalid format
    """
    try:
        # Fetch the ground truth file from S3
        content = storage.get_object(path)
        if not content:
            raise HTTPException(status_code=404, detail=f"Ground truth file not found at {path}")

        # Parse JSON
        data = json.loads(content.decode("utf-8"))

        # Convert to response format - handle both list and object with 'entries' key
        entries = []
        # Determine source list: could be plain list or object with entries key
        if isinstance(data, list):
            source_entries = data
        elif isinstance(data, dict):
            source_entries = data.get("entries", [])
        else:
            source_entries = []

        for entry in source_entries:
            # Handle both formats:
            # - Old format: {"document_id": "...", "expected_validity": "..."}
            # - New format: {"filename": "...", "validity": "..."}
            document_id = entry.get("document_id") or entry.get("filename", "")
            expected_validity = entry.get("expected_validity") or entry.get("validity", "UNKNOWN")
            if document_id:  # Only add entries with valid document_id
                entries.append(
                    GroundTruthEntry(
                        document_id=document_id,
                        filename=document_id,  # Use document_id as filename if not separate
                        expected_validity=expected_validity,
                    )
                )

        return GroundTruthDataResponse(entries=entries)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in ground truth file {path}: {e}")
        raise HTTPException(status_code=400, detail="Invalid ground truth file format")
    except Exception as e:
        logger.error(f"Failed to fetch ground truth from {path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_ground_truth_dataset(
    file: UploadFile = File(...),
    filename_col: str | None = None,
    validity_col: str | None = None,
    reason_col: str | None = None,
    storage: StorageClient = Depends(get_storage),
    state: AppState = Depends(get_app_state),
) -> GroundTruthUploadResponse:
    """Upload ground truth file to S3 storage.

    Validates file extension, uploads to the current run's S3 directory,
    and updates run metadata with the ground truth path.

    Args:
        file: Uploaded file (JSON, YAML, or XLSX format).
        storage: S3 storage client for file operations.
        state: Application state containing current run information.

    Returns:
        Response containing success status, S3 path, and filename.

    Raises:
        HTTPException: When no filename provided (400).
        HTTPException: When unsupported file type (400).
        HTTPException: When no active run available (400).
        HTTPException: When S3 upload fails (500).
    """
    try:
        # Validate file extension
        if not file.filename:
            raise bad_request("No filename provided")

        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = {".json", ".yaml", ".yml", ".xlsx"}
        if file_ext not in allowed_extensions:
            raise bad_request(f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}")

        # Save to the current run's directory instead of creating a new one
        if not state.current_storage_prefix:
            raise bad_request("No active run to upload ground truth to")

        # Always save as ground_truth.json for consistency
        gt_storage_key = f"{state.current_storage_prefix}/ground_truth.json"

        # Handle Excel files - convert to JSON format
        if file_ext == ".xlsx":
            import pandas as pd

            file.file.seek(0)
            df = pd.read_excel(file.file)

            logger.info(f"Excel file columns: {list(df.columns)}")
            logger.info(f"Excel file shape: {df.shape}")

            # Validate required columns exist
            # Use custom column names if provided, otherwise auto-detect
            detected_filename_col = None
            detected_validity_col = None
            detected_reason_col = None

            # Map common column name variations to expected columns
            filename_variations = [
                "Document name",
                "Document Name",
                "filename",
                "Filename",
                "Document",
                "document",
            ]
            validity_variations = [
                "Valid/Invalid",
                "validity",
                "Validity",
                "Status",
                "status",
            ]
            reason_variations = [
                "Reason for Invalidity",
                "Reason for invalidity",
                "reason",
                "Reason",
                "reasoning",
                "Reasoning",
                "explanation",
                "Explanation",
                "notes",
                "Notes",
            ]

            # If custom column names provided, use them directly
            if filename_col and filename_col in df.columns:
                detected_filename_col = filename_col
            if validity_col and validity_col in df.columns:
                detected_validity_col = validity_col
            if reason_col and reason_col in df.columns:
                detected_reason_col = reason_col

            # Auto-detect remaining columns from variations
            for col in df.columns:
                if col in filename_variations and detected_filename_col is None:
                    detected_filename_col = col
                if col in validity_variations and detected_validity_col is None:
                    detected_validity_col = col
                if col in reason_variations and detected_reason_col is None:
                    detected_reason_col = col

            # Use detected values
            filename_col = detected_filename_col
            validity_col = detected_validity_col
            reason_col = detected_reason_col

            if not filename_col:
                raise bad_request(
                    f"Required column not found. Expected one of: {', '.join(filename_variations)}. Found: {', '.join(df.columns)}"
                )

            if not validity_col:
                raise bad_request(
                    f"Required column not found. Expected one of: {', '.join(validity_variations)}. Found: {', '.join(df.columns)}"
                )

            logger.info(f"Using columns: filename='{filename_col}', validity='{validity_col}', reason='{reason_col}'")

            # Convert DataFrame to ground truth format
            ground_truth_list = []
            skipped_rows = []

            for idx, row in df.iterrows():
                # Get filename with proper NaN handling
                filename_value = row[filename_col]
                if pd.isna(filename_value) or str(filename_value).strip() == "":
                    skipped_rows.append(f"Row {idx}: empty filename")
                    continue

                filename = str(filename_value).strip()

                # Get validity with proper NaN handling
                validity_value = row[validity_col]
                if pd.isna(validity_value):
                    validity = "UNKNOWN"
                else:
                    validity_raw = str(validity_value).strip().upper()
                    # Map validity values
                    if validity_raw in ("VALID", "V"):
                        validity = "VALID"
                    elif validity_raw in ("INVALID", "I"):
                        validity = "INVALID"
                    elif validity_raw in (
                        "CLARIFICATION_NEEDED",
                        "CLARIFICATION NEEDED",
                        "C",
                    ):
                        validity = "CLARIFICATION_NEEDED"
                    else:
                        validity = "UNKNOWN"
                        logger.warning(
                            f"Row {idx}: unrecognised validity value '{validity_raw}', defaulting to UNKNOWN"
                        )

                # Add extension if not present
                # Check for real file extensions, not just any dot (e.g., "ST." in street names)
                known_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
                file_ext = Path(filename).suffix.lower()
                if file_ext not in known_extensions:
                    # No recognized extension - add .pdf
                    filename = f"{filename}.pdf"
                    logger.debug(f"Row {idx}: Added .pdf extension to '{filename_value}' -> '{filename}'")

                # Extract reason if column exists
                reason = None
                if reason_col:
                    reason_value = row[reason_col]
                    if pd.notna(reason_value) and str(reason_value).strip():
                        reason = str(reason_value).strip()

                entry = {"filename": filename, "validity": validity}
                if reason:
                    entry["reason"] = reason
                ground_truth_list.append(entry)

            # Log skipped rows
            if skipped_rows:
                logger.warning(f"Skipped {len(skipped_rows)} rows: {'; '.join(skipped_rows)}")

            # Convert to JSON and upload
            json_content = json.dumps(ground_truth_list, indent=2)
            json_bytes = json_content.encode("utf-8")
            file_obj = io.BytesIO(json_bytes)
            file_obj.seek(0)

            if not storage.upload_fileobj(file_obj, gt_storage_key):
                raise internal_error("Failed to upload converted JSON to storage")

            logger.info(
                f"Converted Excel file to JSON and uploaded as: {gt_storage_key} ({len(ground_truth_list)} entries)"
            )
        else:
            # For JSON/YAML files, upload as-is with standardised name
            file.file.seek(0)
            if not storage.upload_fileobj(file.file, gt_storage_key):
                raise internal_error("Failed to upload file to storage")

            logger.info(f"Uploaded ground truth file to S3: {gt_storage_key}")

        # Update run metadata with ground truth path
        update_run_metadata(state.current_storage_prefix, {"ground_truth_path": gt_storage_key})

        # Update database Run record to mark as having ground truth
        # This ensures the UI shows ground truth is available
        try:
            from backend.database.connection import get_session_maker

            Session = get_session_maker()
            with Session() as db:
                # Extract run_id from storage_prefix (format: runs/run_TIMESTAMP)
                run_id = state.current_storage_prefix.rstrip("/").split("/")[-1]
                db_run = db.query(DBRun).filter(DBRun.run_id == run_id).first()
                if db_run:
                    db_run.has_ground_truth = True
                    db_run.ground_truth_path = gt_storage_key
                    db.commit()
                    logger.info(f"Updated database for run {run_id}: has_ground_truth=True")
                else:
                    logger.warning(f"Run {run_id} not found in database")
        except Exception as e:
            logger.error(f"Failed to update database with ground truth flag: {e}", exc_info=True)
            # Don't fail the upload if database update fails

        # Get entries count - for Excel it's in ground_truth_list, for JSON/YAML we need to parse
        entries_count = 0
        if file_ext == ".xlsx":
            entries_count = len(ground_truth_list)
        else:
            # For JSON/YAML, parse to count entries
            try:
                file.file.seek(0)
                content = file.file.read()
                # Try UTF-8 first, then fall back to other encodings
                text_content = None
                for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                    try:
                        text_content = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                if text_content is None:
                    raise ValueError("Could not decode file with any supported encoding")

                if file_ext == ".json":
                    data = json.loads(text_content)
                else:  # YAML
                    import yaml

                    data = yaml.safe_load(text_content)
                # Handle both list and object with 'entries' key
                if isinstance(data, list):
                    entries_count = len(data)
                elif isinstance(data, dict):
                    entries_count = len(data.get("entries", data.get("items", [])))
            except Exception as e:
                logger.warning(f"Could not count entries in uploaded file: {e}")

        return GroundTruthUploadResponse(
            success=True,
            ground_truth_path=gt_storage_key,
            filename="ground_truth.json",
            entries_count=entries_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_error(
            e,
            context={
                "operation": "upload_ground_truth",
                "filename": file.filename if file.filename else "unknown",
            },
        )


@router.post("")
async def get_ground_truth_data(
    request: GroundTruthPathRequest,
) -> GroundTruthDataResponse:
    """Load existing ground truth file and return entries.

    Extracts the S3 prefix from the ground truth path, loads the file from S3,
    and converts ground truth records into response entries.

    Args:
        request: Request containing the ground truth file path.

    Returns:
        Response containing success status and list of ground truth entries
        with document IDs, filenames, and expected validity values.

    Raises:
        HTTPException: When ground truth loading fails (500).
    """
    try:
        # Extract storage_prefix from ground_truth_path if it's an S3 path
        # S3 paths look like: runs/run_20251009_114430/ground_truth.json
        storage_prefix = None
        if request.ground_truth_path and "/" in request.ground_truth_path:
            # Extract the directory part (everything before /ground_truth.json)
            storage_prefix = request.ground_truth_path.rsplit("/", 1)[0]

        # Load ground truth with storage_prefix to satisfy validation
        ground_truth_list = load_ground_truth_dataset(
            storage_prefix=storage_prefix, ground_truth_path=request.ground_truth_path
        )

        # Convert list[GroundTruthDocument] to list of entries
        # Filter out documents without validity labels (prediction mode)
        entries = [
            GroundTruthEntry(
                document_id=gt.document.document_id,
                filename=gt.document.filename,
                expected_validity=gt.expected_validity,
            )
            for gt in ground_truth_list
            if gt.expected_validity is not None
        ]

        return GroundTruthDataResponse(success=True, entries=entries)
    except Exception as e:
        raise handle_error(
            e,
            context={
                "operation": "get_ground_truth_data",
                "path": request.ground_truth_path,
            },
        )


@router.post("/save")
async def save_ground_truth(
    request: SaveGroundTruthRequest,
    storage: StorageClient = Depends(get_storage),
    state: AppState = Depends(get_app_state),
    db: Session = Depends(get_db_session),
) -> GroundTruthSaveResponse:
    """Save ground truth entries to a file.

    Converts request entries to ground truth format, filters out UNKNOWN values,
    uploads to S3 (either in the current run directory or standalone location),
    updates run metadata, and recomputes document correctness and overall accuracy
    in the database.

    Args:
        request: Request containing ground truth entries and optional data directory.
        storage: S3 storage client for file operations.
        state: Application state containing current run information.
        db: Database session for updating run and document records.

    Returns:
        Response containing success status, S3 path, and count of saved entries.

    Raises:
        HTTPException: When neither active run nor data_dir provided (400).
        HTTPException: When S3 upload fails (500).
    """
    try:
        # Convert entries to the format expected by load_ground_truth
        # It expects a list of dicts with 'filename' and 'validity' keys
        ground_truth_list = [
            {
                "filename": entry["document_id"],
                "validity": entry["expected_validity"],
            }
            for entry in request.entries
        ]

        # Determine S3 key based on whether we have an active run or standalone creation
        if state.current_storage_prefix:
            # Active run: save to current run directory
            run_prefix = state.current_storage_prefix.rstrip("/")
            storage_key = f"{run_prefix}/ground_truth.json"
        elif request.data_dir:
            # Standalone: create ground truth based on data_dir
            # Sanitise data_dir to create a safe S3 key (not for security)
            dir_hash = hashlib.md5(  # nosec B324
                request.data_dir.encode(), usedforsecurity=False
            ).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_prefix = f"ground_truth/{dir_hash}_{timestamp}"
            storage_key = f"{run_prefix}/ground_truth.json"
            logger.info(f"Creating standalone ground truth for data_dir: {request.data_dir} at {storage_key}")
        else:
            raise bad_request("Either an active run or data_dir must be provided")

        # Filter out UNKNOWN values before saving
        # UNKNOWN means "no ground truth" and shouldn't be saved as explicit ground truth
        valid_ground_truth = [
            entry for entry in ground_truth_list if entry.get("validity", "").upper() not in ["UNKNOWN", ""]
        ]

        logger.info(
            f"Filtered ground truth: {len(valid_ground_truth)} valid entries out of {len(ground_truth_list)} total"
        )

        # Upload to S3
        json_content = json.dumps(valid_ground_truth, indent=2)
        json_bytes = json_content.encode("utf-8")
        file_obj = io.BytesIO(json_bytes)
        file_obj.seek(0)  # Reset file pointer to beginning for upload

        if not storage.upload_fileobj(file_obj, storage_key):
            raise internal_error("Failed to save ground truth to storage")

        logger.info(f"Saved ground truth file to S3: {storage_key} with {len(valid_ground_truth)} entries")

        # Update run metadata with ground truth path (only if we have an active run)
        if state.current_storage_prefix:
            update_run_metadata(run_prefix, {"ground_truth_path": storage_key})

        # Update database with ground truth and recompute correctness
        # Extract run_id from storage_prefix (format: runs/run_TIMESTAMP)
        # This works whether we have an active run or using data_dir
        try:
            run_id = run_prefix.split("/")[-1]

            db_run = db.query(DBRun).filter(DBRun.run_id == run_id).first()
            if db_run:
                # Create a map of document_id -> expected_validity (only for valid entries)
                ground_truth_map = {entry["filename"]: entry["validity"] for entry in valid_ground_truth}

                # Update each document with ground truth and recompute correctness
                updated_count = 0
                for db_doc in db_run.documents:
                    expected = ground_truth_map.get(db_doc.document_id)
                    if expected:
                        db_doc.expected_validity = expected
                        # Recompute correctness
                        if db_doc.predicted_validity and expected:
                            db_doc.is_correct = db_doc.predicted_validity.upper() == expected.upper()
                        updated_count += 1

                # Mark run as having ground truth
                db_run.has_ground_truth = True

                # Recompute overall accuracy
                correct_count = sum(1 for doc in db_run.documents if doc.is_correct)
                total_count = len(db_run.documents)
                if total_count > 0:
                    db_run.overall_accuracy = correct_count / total_count

                db.commit()
                logger.info(f"Updated {updated_count} documents with ground truth for run {run_id}")
            else:
                logger.warning(f"Run {run_id} not found in database")
        except Exception as e:
            logger.error(f"Failed to update database with ground truth: {e}", exc_info=True)

        return GroundTruthSaveResponse(
            success=True,
            ground_truth_path=storage_key,
            entries_count=len(ground_truth_list),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_error(
            e,
            context={
                "operation": "save_ground_truth",
                "storage_key": storage_key if "storage_key" in locals() else None,
            },
        )


@router.post("/update-document")
async def update_document_ground_truth(
    request: UpdateDocumentGroundTruthRequest,
    storage: StorageClient = Depends(get_storage),
    state: AppState = Depends(get_app_state),
    db: Session = Depends(get_db_session),
) -> GroundTruthUpdateResponse:
    """Update ground truth label for a single document.

    Validates the expected validity value, loads the existing ground truth file
    from S3, updates or adds the document's entry, saves the modified file back
    to S3, and updates the database record with the new ground truth value and
    recomputed correctness and accuracy metrics.

    Args:
        request: Request containing document ID, expected validity, and optional run ID.
        storage: S3 storage client for file operations.
        state: Application state containing current run information.
        db: Database session for updating document and run records.

    Returns:
        Response containing success status and confirmation message.

    Raises:
        HTTPException: When expected_validity is empty or UNKNOWN (400).
        HTTPException: When no active run and no run_id provided (400).
        HTTPException: When S3 save operation fails (500).
    """
    try:
        # Validate that expected_validity is not UNKNOWN or empty
        if not request.expected_validity or request.expected_validity.upper() == "UNKNOWN":
            raise bad_request(
                "Cannot set ground truth to empty or 'UNKNOWN'. Please select a valid label (VALID, INVALID, or CLARIFICATION_NEEDED)."
            )

        # Determine storage_prefix from either current run or provided run_id
        storage_prefix = None
        if request.run_id:
            # Historical run - construct storage_prefix from run_id
            storage_prefix = f"runs/{request.run_id}"
            logger.info(f"Updating ground truth for historical run: {request.run_id}")
        elif state.current_storage_prefix:
            # Active run
            storage_prefix = state.current_storage_prefix.rstrip("/")
            logger.info(f"Updating ground truth for active run: {storage_prefix}")
        else:
            logger.error("No active run and no run_id provided")
            raise bad_request("No active run and no run_id provided")

        # Load existing ground truth file
        ground_truth_key = f"{storage_prefix}/ground_truth.json"
        ground_truth_data = []

        try:
            content = storage.get_object(ground_truth_key)
            if content:
                ground_truth_data = json.loads(content.decode("utf-8"))
        except Exception as e:
            logger.warning(f"Could not load existing ground truth: {e}")

        # Update or add the document's ground truth
        updated = False
        for entry in ground_truth_data:
            if entry.get("filename") == request.document_id:
                entry["validity"] = request.expected_validity
                updated = True
                break

        if not updated:
            ground_truth_data.append({"filename": request.document_id, "validity": request.expected_validity})

        # Save updated ground truth
        json_content = json.dumps(ground_truth_data, indent=2)
        json_bytes = json_content.encode("utf-8")
        file_obj = io.BytesIO(json_bytes)
        file_obj.seek(0)

        if not storage.upload_fileobj(file_obj, ground_truth_key):
            raise internal_error("Failed to save updated ground truth")

        logger.info(f"Updated ground truth for document {request.document_id}")

        # Update database
        run_id = request.run_id or storage_prefix.split("/")[-1]
        db_run = db.query(DBRun).filter(DBRun.run_id == run_id).first()
        if db_run:
            for db_doc in db_run.documents:
                if db_doc.document_id == request.document_id:
                    db_doc.expected_validity = request.expected_validity
                    # Recompute correctness
                    if db_doc.predicted_validity:
                        db_doc.is_correct = db_doc.predicted_validity.upper() == request.expected_validity.upper()
                    break

            # Mark run as having ground truth
            db_run.has_ground_truth = True

            # Recompute overall accuracy
            correct_count = sum(1 for doc in db_run.documents if doc.is_correct)
            total_count = len(db_run.documents)
            if total_count > 0:
                db_run.overall_accuracy = correct_count / total_count

            db.commit()

        return GroundTruthUpdateResponse(success=True, message=f"Updated ground truth for {request.document_id}")

    except HTTPException:
        raise
    except Exception as e:
        raise handle_error(
            e,
            context={
                "operation": "update_document_ground_truth",
                "document_id": request.document_id,
            },
        )
