"""
MinIO client — handles image upload/download for leaf images.
"""

import io
import uuid
from datetime import timedelta
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.config import get_settings

settings = get_settings()


class MinioClient:
    """MinIO client wrapper for image storage operations."""

    def __init__(self):
        self._client: Optional[Minio] = None

    def connect(self):
        """Initialize MinIO client and ensure the bucket exists."""
        self._client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )

        # Create bucket if it doesn't exist
        if not self._client.bucket_exists(settings.MINIO_BUCKET_NAME):
            self._client.make_bucket(settings.MINIO_BUCKET_NAME)

    def upload_image(self, user_id: str, image_bytes: bytes, content_type: str = "image/jpeg") -> str:
        """
        Upload an image to MinIO.
        Returns the object name (path within the bucket).
        """
        # Generate unique filename: user_id/uuid.ext
        ext = "png" if "png" in content_type else "jpg"
        object_name = f"{user_id}/{uuid.uuid4()}.{ext}"

        self._client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=io.BytesIO(image_bytes),
            length=len(image_bytes),
            content_type=content_type,
        )

        return object_name

    def get_image_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Generate a presigned URL to access an image.
        Default expiry: 1 hour.
        """
        try:
            return self._client.presigned_get_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=object_name,
                expires=timedelta(seconds=expires),
            )
        except S3Error:
            return ""

    def delete_image(self, object_name: str):
        """Delete an image from MinIO."""
        try:
            self._client.remove_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=object_name,
            )
        except S3Error:
            pass


# Singleton instance
minio_client = MinioClient()
