"""Servicio MinIO para almacenamiento de medios."""
from __future__ import annotations

import io
import json
import logging
import uuid
from pathlib import PurePosixPath
from typing import BinaryIO

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

EXT_BY_MIME = {
    "image/webp": "webp",
    "image/jpeg": "jpg",
    "image/png": "png",
    "application/pdf": "pdf",
}


def _normalize_public_url_base(base_url: str, bucket: str) -> str:
    normalized = (base_url or "").rstrip("/")
    bucket_suffix = f"/{bucket}"
    if normalized.endswith(bucket_suffix):
        return normalized[: -len(bucket_suffix)]
    return normalized


def _public_read_policy(bucket: str) -> str:
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                    "Resource": [f"arn:aws:s3:::{bucket}"],
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/*"],
                },
            ],
        }
    )


class MinioService:
    def __init__(self) -> None:
        self.client: Minio | None = None
        self.bucket: str = ""
        self.public_url_base: str = ""

    def init_app(self, app) -> None:
        endpoint = app.config.get("MINIO_ENDPOINT")
        access = app.config.get("MINIO_ACCESS_KEY")
        secret = app.config.get("MINIO_SECRET_KEY")
        secure = bool(app.config.get("MINIO_SECURE"))
        self.bucket = app.config.get("MINIO_BUCKET", "lavalleja-cms")
        public_url_base = (
            app.config.get("MINIO_PUBLIC_URL")
            or f"{'https' if secure else 'http'}://{endpoint}"
        ).rstrip("/")
        self.public_url_base = _normalize_public_url_base(
            public_url_base,
            self.bucket,
        )

        if not endpoint or not access or not secret:
            logger.warning(
                "MinIO no configurado "
                "(faltan credenciales). Servicio deshabilitado."
            )
            return

        try:
            self.client = Minio(
                endpoint,
                access_key=access,
                secret_key=secret,
                secure=secure,
            )
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
            self.client.set_bucket_policy(
                self.bucket,
                _public_read_policy(self.bucket),
            )
            logger.info("MinIO listo: bucket=%s", self.bucket)
        except Exception as exc:
            logger.warning(
                "MinIO init fallo (%s). Continuamos sin uploads.",
                exc,
            )
            self.client = None

    def _ext_for(self, mime: str, original_name: str | None) -> str:
        if mime in EXT_BY_MIME:
            return EXT_BY_MIME[mime]
        if original_name and "." in original_name:
            return original_name.rsplit(".", 1)[-1].lower()[:6]
        return "bin"

    def upload_bytes(self, data: bytes, mime: str, *, prefix: str = "uploads",
                     original_name: str | None = None) -> dict:
        if not self.client:
            raise RuntimeError("MinIO no esta configurado")
        ext = self._ext_for(mime, original_name)
        object_name = str(PurePosixPath(prefix) / f"{uuid.uuid4().hex}.{ext}")
        stream = io.BytesIO(data)
        try:
            self.client.put_object(
                self.bucket,
                object_name,
                stream,
                length=len(data),
                content_type=mime,
            )
        except S3Error as exc:
            raise RuntimeError(f"S3 error: {exc}") from exc
        return {
            "object_name": object_name,
            "bucket": self.bucket,
            "public_url": self.url_for(object_name),
            "size": len(data),
        }

    def upload_stream(
        self,
        stream: BinaryIO,
        mime: str,
        *,
        prefix: str = "uploads",
        original_name: str | None = None,
    ) -> dict:
        data = stream.read()
        return self.upload_bytes(
            data,
            mime,
            prefix=prefix,
            original_name=original_name,
        )

    def url_for(self, object_name: str) -> str:
        return f"{self.public_url_base}/{self.bucket}/{object_name}"

    def remove(self, object_name: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.remove_object(self.bucket, object_name)
            return True
        except Exception as exc:
            logger.warning("MinIO remove fallo: %s", exc)
            return False


minio_service = MinioService()
