"""Private S3 storage for generated clinical documents."""

from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config.settings import settings


class DocumentStorageError(RuntimeError):
    """Raised when a document cannot be stored or shared from S3."""


@dataclass(frozen=True)
class StoredDocument:
    object_key: str
    url: str
    expires_in_seconds: int


def _s3_client():
    """Build a client lazily so application startup does not need AWS access."""
    kwargs = {}
    if settings.AWS_REGION:
        kwargs["region_name"] = settings.AWS_REGION
    return boto3.client("s3", **kwargs)


def _object_key(document_type: str, document_id: int, filename: str) -> str:
    prefix = settings.DOCUMENTS_S3_PREFIX.strip("/")
    return f"{prefix}/{document_type}/{document_id}/{filename}"


def upload_document(pdf_path: str, document_type: str, document_id: int) -> StoredDocument:
    """Upload a PDF privately and return a short-lived, downloadable URL."""
    if not settings.DOCUMENTS_S3_BUCKET:
        raise DocumentStorageError("DOCUMENTS_S3_BUCKET is not configured")
    if not 1 <= settings.DOCUMENT_LINK_EXPIRY_SECONDS <= 604800:
        raise DocumentStorageError(
            "DOCUMENT_LINK_EXPIRY_SECONDS must be between 1 and 604800"
        )

    file_path = Path(pdf_path)
    if not file_path.is_file():
        raise DocumentStorageError(f"Generated document does not exist: {file_path}")

    key = _object_key(document_type, document_id, file_path.name)
    upload_args = {
        "ContentType": "application/pdf",
        "ContentDisposition": f'attachment; filename="{file_path.name}"',
        "ServerSideEncryption": settings.DOCUMENTS_S3_ENCRYPTION,
        "Metadata": {
            "document-type": document_type,
            "document-id": str(document_id),
        },
    }
    if settings.DOCUMENTS_S3_KMS_KEY_ID:
        upload_args["SSEKMSKeyId"] = settings.DOCUMENTS_S3_KMS_KEY_ID

    try:
        client = _s3_client()
        client.upload_file(
            str(file_path), settings.DOCUMENTS_S3_BUCKET, key, ExtraArgs=upload_args
        )
        url = client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.DOCUMENTS_S3_BUCKET,
                "Key": key,
                "ResponseContentType": "application/pdf",
                "ResponseContentDisposition": f'attachment; filename="{file_path.name}"',
            },
            ExpiresIn=settings.DOCUMENT_LINK_EXPIRY_SECONDS,
        )
    except (BotoCoreError, ClientError) as exc:
        raise DocumentStorageError("Unable to upload document to S3") from exc

    return StoredDocument(
        object_key=key,
        url=url,
        expires_in_seconds=settings.DOCUMENT_LINK_EXPIRY_SECONDS,
    )
