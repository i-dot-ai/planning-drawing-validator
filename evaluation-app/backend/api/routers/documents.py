import logging
from urllib.parse import unquote

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from planning_drawing_validator.config import get_config
from planning_drawing_validator.exceptions import DocumentNotFoundError
from planning_drawing_validator.types import Filename

from backend.api.dependencies import get_app_state, get_storage
from backend.api.error_handlers import bad_request, handle_error, not_found
from backend.api.models.responses import (
    DocumentInfo,
    DocumentInfoResponse,
    DocumentListResponse,
    DocumentUploadResponse,
    UploadedFileInfo,
)
from backend.config import CacheConstants
from backend.services.document_service import DocumentResolver, FileUploader
from backend.services.run_metadata_service import RunMetadataService
from backend.state import AppState
from backend.storage.client import StorageClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])

_, path_config = get_config()


@router.post("/upload")
async def upload_documents(
    files: list[UploadFile] = File(...),
    storage: StorageClient = Depends(get_storage),
    state: AppState = Depends(get_app_state),
) -> DocumentUploadResponse:
    """Upload documents to S3 storage with content-addressable hashing.

    Uploads multiple document files to S3 storage using SHA-256 content-addressable
    hashing for deduplication. Creates a new run with unique ID and metadata tracking.
    Files with identical content hashes are stored only once and referenced by hash.

    Args:
        files: List of uploaded files to process and store.
        storage: S3 storage client for file operations.
        state: Application state for tracking current run.

    Returns:
        DocumentUploadResponse containing run ID, S3 prefix, file count, and detailed
        information for each uploaded file including content hashes and deduplication status.

    Raises:
        HTTPException: When file upload or metadata creation fails (500).
    """
    try:
        metadata_service = RunMetadataService(storage)

        # Generate run ID and name
        run_id, run_name = metadata_service.generate_run_id()
        storage_prefix = f"runs/{run_id}/"

        logger.info(f"Upload endpoint called with {len(files)} files for run {run_id}")

        # Upload files using service
        uploader = FileUploader(storage, run_id)
        uploaded_files = []

        for file in files:
            if not file.filename:
                logger.warning("Skipping file with no filename")
                continue

            # Read file content
            file.file.seek(0)
            content = file.file.read()

            # Upload with deduplication
            try:
                uploaded_file = uploader.upload_file(file.filename, content, file.content_type)
                uploaded_files.append(uploaded_file)
                logger.info(
                    f"Uploaded {file.filename} (hash: {uploaded_file.content_hash}, deduped: {uploaded_file.deduped})"
                )
            except Exception as e:
                logger.error(f"Failed to upload {file.filename}: {e}")
                raise

        logger.info(f"Successfully uploaded {len(uploaded_files)} files for run {run_id}")

        # Create run metadata in S3 (source of truth for uploaded documents)
        # Note: Database run record is created when evaluation starts, not during upload
        metadata_service.create_run_metadata(run_id, run_name, storage_prefix, uploaded_files)

        # Update app state
        state.current_storage_prefix = storage_prefix.rstrip("/")

        # Return response
        file_infos = [
            UploadedFileInfo(
                filename=f.filename,
                document_id=f.document_id,
                content_hash=f.content_hash,
                storage_key=f.storage_key,
                deduped=f.deduped,
            )
            for f in uploaded_files
        ]

        return DocumentUploadResponse(
            success=True,
            data_dir=storage_prefix,
            storage_prefix=storage_prefix,
            run_id=run_id,
            file_count=len(uploaded_files),
            run_name=run_name,
            files=file_infos,
        )
    except Exception as e:
        raise handle_error(e, context={"operation": "upload_documents", "file_count": len(files)})


@router.get("")
async def list_documents(
    state: AppState = Depends(get_app_state),
) -> DocumentListResponse:
    """List available documents for evaluation.

    Returns documents from run metadata as the single source of truth. Falls back
    to local directory scanning if no S3 prefix is configured. Documents are
    identified by their document_id (filename without directory path or extension).

    Args:
        state: Application state containing current S3 prefix or data directory.

    Returns:
        DocumentListResponse containing list of documents with their IDs and filenames.

    Raises:
        HTTPException: When document listing fails (500).
    """
    try:
        # Read from run metadata file
        if state.current_storage_prefix:
            from backend.services.run_metadata_service import get_run_metadata

            metadata = get_run_metadata(state.current_storage_prefix)
            if metadata and metadata.get("files"):
                documents = []
                for file_info in metadata["files"]:
                    # Use document_id from metadata (filename without dir/extension)
                    # Fallback to computing it if not present in older metadata
                    if "document_id" in file_info:
                        document_id = file_info["document_id"]
                    else:
                        # Fallback: compute from filename for backwards compatibility
                        orig_filename = file_info["filename"]
                        filename_only = orig_filename.split("/")[-1]
                        document_id = filename_only.rsplit(".", 1)[0] if "." in filename_only else filename_only

                    documents.append(
                        DocumentInfo(
                            document_id=document_id,
                            filename=file_info["filename"],
                        )
                    )

                logger.info(f"Found {len(documents)} documents from metadata for {state.current_storage_prefix}")
                return DocumentListResponse(documents=documents)

        # Fallback to local directory
        if path_config.data_dir.exists():
            documents = []
            for pdf_file in path_config.data_dir.glob("*.pdf"):
                document_id = pdf_file.stem
                documents.append(
                    DocumentInfo(
                        document_id=document_id,
                        filename=pdf_file.name,
                    )
                )
            return DocumentListResponse(documents=documents)

        return DocumentListResponse(documents=[])

    except Exception as e:
        raise handle_error(e, context={"operation": "list_documents"})


@router.get("/{filename}/pdf")
async def serve_pdf(
    filename: Filename,
    storage: StorageClient = Depends(get_storage),
    state: AppState = Depends(get_app_state),
) -> StreamingResponse:
    """Serve PDF files for the document viewer.

    Streams PDF documents from S3 or local storage with appropriate headers for
    inline browser display. Validates that the requested file is actually a PDF.

    Args:
        filename: URL-encoded filename of the PDF document to serve.
        storage: S3 storage client for file retrieval.
        state: Application state containing current S3 prefix or data directory.

    Returns:
        StreamingResponse with PDF content, mime type, and caching headers.

    Raises:
        HTTPException: When document is not found (404), not a PDF (400), or
            retrieval fails (500).

    Note:
        Legacy endpoint - prefer using /{filename}/file for all document types.
    """
    try:
        decoded_filename = unquote(filename)
        resolver = DocumentResolver(storage)

        # Get document stream (raises DocumentNotFoundError if not found)
        generator, mime_type, size, resolved_name = resolver.get_document_stream(
            decoded_filename,
            storage_prefix=state.current_storage_prefix,
            data_dir=state.current_data_dir,
        )

        # Verify it's a PDF file
        if not resolved_name.lower().endswith(".pdf"):
            raise bad_request("File is not a PDF")

        return StreamingResponse(
            generator,
            media_type=mime_type or "application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={resolved_name}",
                "Content-Length": str(size),
                "Cache-Control": CacheConstants.DOCUMENT_CACHE_CONTROL,
                "Accept-Ranges": "bytes",
            },
        )
    except DocumentNotFoundError as e:
        logger.warning(f"Document not found: {filename} - {e.details}")
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to serve PDF {filename}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{filename}/file")
async def serve_document_file(
    filename: Filename,
    storage: StorageClient = Depends(get_storage),
    state: AppState = Depends(get_app_state),
) -> StreamingResponse:
    """Serve document file from S3 or local storage.

    Streams document files (PDF or images) with automatic content-type detection
    and browser-appropriate headers. Supports content-addressable lookup using
    document hashes from run metadata.

    Args:
        filename: URL-encoded filename or content hash of the document to serve.
        storage: S3 storage client for file retrieval.
        state: Application state containing current S3 prefix or data directory.

    Returns:
        StreamingResponse with document content, detected mime type, and caching headers.

    Raises:
        HTTPException: When document is not found (404) or retrieval fails (500).
    """
    try:
        decoded_filename = unquote(filename)
        resolver = DocumentResolver(storage)

        # Get document stream (raises DocumentNotFoundError if not found)
        generator, mime_type, size, resolved_name = resolver.get_document_stream(
            decoded_filename,
            storage_prefix=state.current_storage_prefix,
            data_dir=state.current_data_dir,
        )

        return StreamingResponse(
            generator,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename={resolved_name}",
                "Content-Length": str(size),
                "Cache-Control": CacheConstants.DOCUMENT_CACHE_CONTROL,
                "Accept-Ranges": "bytes",
            },
        )
    except DocumentNotFoundError as e:
        logger.warning(f"Document not found: {filename} - {e.details}")
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to serve document file {filename}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{filename}/info")
async def document_info(
    filename: Filename,
    storage: StorageClient = Depends(get_storage),
    state: AppState = Depends(get_app_state),
) -> DocumentInfoResponse:
    """Return document metadata including content type and size.

    Resolves document metadata without streaming the full content. Provides
    information needed for document handling including mime type, file size,
    and resolved filename after content-addressable hash lookup.

    Args:
        filename: URL-encoded filename or content hash of the document.
        storage: S3 storage client for metadata retrieval.
        state: Application state containing current S3 prefix or data directory.

    Returns:
        DocumentInfoResponse containing resolved filename, mime type, size in bytes,
        and optional URL for local file access.

    Raises:
        HTTPException: When document is not found (404) or metadata retrieval fails (500).
    """
    try:
        decoded_filename = unquote(filename)
        resolver = DocumentResolver(storage)

        doc_info = resolver.resolve_document(
            decoded_filename,
            storage_prefix=state.current_storage_prefix,
            data_dir=state.current_data_dir,
        )

        if not doc_info:
            raise not_found(f"Document not found: {decoded_filename}")

        # Add URL for local files
        url = None
        if doc_info.local_path:
            url = f"/api/documents/{doc_info.resolved_filename}/file"

        return DocumentInfoResponse(
            resolved_filename=doc_info.resolved_filename,
            mime_type=doc_info.mime_type,
            size=doc_info.size,
            url=url,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_error(e, context={"operation": "get_document_info", "filename": filename})
