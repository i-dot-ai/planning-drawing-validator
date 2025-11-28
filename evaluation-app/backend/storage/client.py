import io
import logging
import os
from pathlib import Path
from typing import Any, BinaryIO, cast

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class StorageClient:
    """S3-compatible storage client for document management.

    This class implements both ReadOnlyStorageProtocol and ReadWriteStorageProtocol
    from the planning-drawing-validator core package. The validator only uses the
    read-only methods, while the application uses the full read-write capabilities
    for document lifecycle management.

    Protocol Methods:
        ReadOnlyStorageProtocol (for validator):
            - get_document(identifier) -> bytes
            - document_exists(identifier) -> bool
            - find_document(prefix, filename) -> str | None

        ReadWriteStorageProtocol (for application):
            - write_document(identifier, content) -> None
            - delete_document(identifier) -> None

    Additional S3-specific methods:
        - upload_file, upload_fileobj (alternative upload methods)
        - get_object_stream, get_object_streaming_body (streaming downloads)
        - generate_presigned_url (temporary access URLs)
        - get_object_metadata (file metadata without downloading)
    """

    def __init__(self) -> None:
        """Initialise storage client with environment configuration.

        Raises:
            ValueError: If required S3 credentials are not set in environment.
        """
        self.endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000")
        self.access_key = os.getenv("S3_ACCESS_KEY")
        self.secret_key = os.getenv("S3_SECRET_KEY")
        self.bucket = os.getenv("S3_BUCKET", "review-documents")
        self.secure = os.getenv("S3_SECURE", "false").lower() == "true"

        # Validate required credentials
        if not self.access_key or not self.secret_key:
            raise ValueError(
                "S3_ACCESS_KEY and S3_SECRET_KEY environment variables must be set. "
                "For local development with MinIO, set S3_ACCESS_KEY=minioadmin and S3_SECRET_KEY=minioadmin123. "
                "For production, use secure credentials."
            )

        # Initialise S3 client
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4"),
            use_ssl=self.secure,
        )

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket {self.bucket} exists")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                logger.info(f"Creating bucket {self.bucket}")
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket)
                    logger.info(f"Bucket {self.bucket} created successfully")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket {self.bucket}: {create_error}")
                    raise
            else:
                logger.error(f"Failed to check bucket {self.bucket}: {e}")
                raise

    def upload_file(self, file_path: Path, object_key: str) -> bool:
        """Upload a file to S3 storage.

        Args:
            file_path: Local path to the file to upload
            object_key: S3 object key (path in bucket)

        Returns:
            True if upload succeeded, False otherwise
        """
        try:
            self.s3_client.upload_file(
                str(file_path),
                self.bucket,
                object_key,
            )
            logger.info(f"Uploaded {file_path} to {object_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload {file_path} to {object_key}: {e}")
            return False

    def upload_fileobj(self, file_obj: BinaryIO, object_key: str) -> bool:
        """Upload a file-like object to S3 storage.

        Args:
            file_obj: File-like object to upload
            object_key: S3 object key (path in bucket)

        Returns:
            True if upload succeeded, False otherwise
        """
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket,
                object_key,
            )
            logger.info(f"Uploaded file object to {object_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file object to {object_key}: {e}")
            return False

    def download_file(self, object_key: str, file_path: Path) -> bool:
        """Download a file from S3 storage.

        Args:
            object_key: S3 object key (path in bucket)
            file_path: Local path to save the file

        Returns:
            True if download succeeded, False otherwise
        """
        try:
            self.s3_client.download_file(
                self.bucket,
                object_key,
                str(file_path),
            )
            logger.info(f"Downloaded {object_key} to {file_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download {object_key} to {file_path}: {e}")
            return False

    def get_object(self, object_key: str) -> bytes | None:
        """Get object content as bytes.

        Args:
            object_key: S3 object key (path in bucket)

        Returns:
            File content as bytes, or None if failed
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            return cast(bytes, response["Body"].read())
        except ClientError as e:
            logger.error(f"Failed to get object {object_key}: {e}")
            return None

    def get_object_stream(self, object_key: str) -> io.BytesIO | None:
        """Get object as a streaming BytesIO object.

        Args:
            object_key: S3 object key (path in bucket)

        Returns:
            BytesIO stream, or None if failed
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            return io.BytesIO(response["Body"].read())
        except ClientError as e:
            logger.error(f"Failed to get object stream {object_key}: {e}")
            return None

    def get_object_streaming_body(self, object_key: str) -> Any | None:
        """Get object as a streaming body for efficient chunked reading.

        Args:
            object_key: S3 object key (path in bucket)

        Returns:
            S3 streaming body object, or None if failed
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            return response["Body"]
        except ClientError as e:
            logger.error(f"Failed to get streaming body {object_key}: {e}")
            return None

    def get_object_metadata(self, object_key: str) -> dict[str, Any] | None:
        """Get object metadata without downloading the content.

        Args:
            object_key: S3 object key (path in bucket)

        Returns:
            Metadata dict with ContentLength, ContentType, etc., or None if failed
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            return {
                "content_length": response.get("ContentLength"),
                "content_type": response.get("ContentType"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag"),
            }
        except ClientError as e:
            logger.error(f"Failed to get object metadata {object_key}: {e}")
            return None

    def object_exists(self, object_key: str) -> bool:
        """Check if an object exists in S3 storage.

        Args:
            object_key: S3 object key (path in bucket)

        Returns:
            True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            return True
        except ClientError:
            return False

    # ReadOnlyStorageProtocol-compatible methods (required by validator)

    def get_document(self, identifier: str) -> bytes:
        """Retrieve document content by identifier (ReadOnlyStorageProtocol method).

        This method conforms to the ReadOnlyStorageProtocol interface defined in the
        core package. It's a wrapper around get_object that raises exceptions
        instead of returning None for error cases.

        Args:
            identifier: S3 object key (document identifier).

        Returns:
            Document content as bytes.

        Raises:
            FileNotFoundError: If document doesn't exist in storage.
        """
        content = self.get_object(identifier)
        if content is None:
            raise FileNotFoundError(f"Document not found in S3 storage: {identifier}")
        return content

    def document_exists(self, identifier: str) -> bool:
        """Check if a document exists (ReadOnlyStorageProtocol method).

        This method conforms to the ReadOnlyStorageProtocol interface. It's an alias
        for object_exists with protocol-compliant naming.

        Args:
            identifier: Document identifier to check.

        Returns:
            True if document exists, False otherwise.
        """
        return self.object_exists(identifier)

    def find_document(self, prefix: str, filename: str) -> str | None:
        """Find a document by filename within a prefix (ReadOnlyStorageProtocol method).

        This method conforms to the ReadOnlyStorageProtocol interface. It searches for
        a document by filename within the specified S3 prefix, checking direct
        key first then listing all objects to find a matching filename.

        Args:
            prefix: S3 prefix to search within.
            filename: Filename to locate.

        Returns:
            Full S3 object key if found, None otherwise.
        """
        # Try direct key first
        direct_key = f"{prefix}/{filename}".lstrip("/")
        if self.object_exists(direct_key):
            return direct_key

        # List and search
        objects = self.list_objects(prefix=prefix)
        for obj_key in objects:
            if obj_key.endswith(filename):
                return obj_key

        return None

    def write_document(self, identifier: str, content: bytes) -> None:
        """Write document content to S3 storage (ReadWriteStorageProtocol method).

        This method conforms to the ReadWriteStorageProtocol interface. It's a wrapper
        around the S3 upload methods that uses the protocol-compliant signature.

        Args:
            identifier: S3 object key where to write the document.
            content: Document content as bytes.

        Raises:
            Exception: If upload fails.
        """
        import io

        file_obj = io.BytesIO(content)
        success = self.upload_fileobj(file_obj, identifier)
        if not success:
            raise Exception(f"Failed to write document to S3: {identifier}")

    def delete_document(self, identifier: str) -> None:
        """Delete a document from S3 storage (ReadWriteStorageProtocol method).

        This method conforms to the ReadWriteStorageProtocol interface. It's a wrapper
        around delete_object that uses the protocol-compliant signature.

        Args:
            identifier: S3 object key to delete.

        Raises:
            FileNotFoundError: If document doesn't exist.
            Exception: If deletion fails.
        """
        if not self.object_exists(identifier):
            raise FileNotFoundError(f"Document not found in S3: {identifier}")

        success = self.delete_object(identifier)
        if not success:
            raise Exception(f"Failed to delete document from S3: {identifier}")

    def list_objects(self, prefix: str = "") -> list[str]:
        """List objects in S3 storage with optional prefix filter.

        Args:
            prefix: Optional prefix to filter objects

        Returns:
            List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
            )
            return [obj["Key"] for obj in response.get("Contents", [])]
        except ClientError as e:
            logger.error(f"Failed to list objects with prefix {prefix}: {e}")
            return []

    def delete_object(self, object_key: str) -> bool:
        """Delete an object from S3 storage.

        Args:
            object_key: S3 object key (path in bucket)

        Returns:
            True if deletion succeeded, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=object_key,
            )
            logger.info(f"Deleted object {object_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete object {object_key}: {e}")
            return False

    def get_presigned_url(self, object_key: str, expiration: int = 3600) -> str | None:
        """Generate a presigned URL for temporary access to an object.

        Args:
            object_key: S3 object key (path in bucket)
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL, or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": object_key,
                },
                ExpiresIn=expiration,
            )
            return cast(str, url)
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {object_key}: {e}")
            return None


# Global storage client instance
_storage_client: StorageClient | None = None


def get_storage_client() -> StorageClient:
    """Get or create the global storage client instance."""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client
