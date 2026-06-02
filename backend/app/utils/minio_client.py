"""
S3-compatible storage client using boto3.
Replaces minio to natively support endpoints with path prefixes (like Supabase S3).
"""

import io
import uuid
from typing import Optional
import boto3
from botocore.client import Config

from app.config import get_settings

settings = get_settings()


class MinioClient:
    """S3 client wrapper for image storage operations."""

    def __init__(self):
        self._client = None

    def connect(self):
        """Initialize S3 client using boto3."""
        endpoint = settings.MINIO_ENDPOINT
        
        # Ensure endpoint has protocol
        if not endpoint.startswith("http"):
            protocol = "https" if settings.MINIO_SECURE else "http"
            endpoint_url = f"{protocol}://{endpoint}"
        else:
            endpoint_url = endpoint

        # Initialize boto3 S3 client
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"}  # Required for custom S3 providers
            ),
            region_name="us-east-1"  # Default region
        )

        # Basic S3 access verification
        try:
            self._client.list_buckets()
        except Exception as e:
            print(f"⚠️ S3 connection test failed or bypassed: {e}")

    def upload_image(self, user_id: str, image_bytes: bytes, content_type: str = "image/jpeg") -> str:
        """
        Upload an image to S3.
        Returns the object name (path within the bucket).
        """
        ext = "png" if "png" in content_type else "jpg"
        object_name = f"{user_id}/{uuid.uuid4()}.{ext}"

        self._client.put_object(
            Bucket=settings.MINIO_BUCKET_NAME,
            Key=object_name,
            Body=io.BytesIO(image_bytes),
            ContentType=content_type,
        )

        return object_name

    def get_image_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Generate a presigned URL to access an image.
        Default expiry: 1 hour.
        """
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": settings.MINIO_BUCKET_NAME,
                    "Key": object_name,
                },
                ExpiresIn=expires,
            )
        except Exception:
            return ""

    def delete_image(self, object_name: str):
        """Delete an image from S3."""
        try:
            self._client.delete_object(
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=object_name,
            )
        except Exception:
            pass


# Singleton instance
minio_client = MinioClient()
