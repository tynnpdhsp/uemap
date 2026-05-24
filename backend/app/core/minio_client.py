import asyncio
from io import BytesIO
from minio import Minio
from app.core.config import settings

class MinioClient:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except Exception as e:
            print(f"Error initializing MinIO bucket: {e}")

    async def put_object(self, object_key: str, data: BytesIO, length: int, content_type: str) -> str:
        def _put():
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                data=data,
                length=length,
                content_type=content_type
            )
            return object_key
        return await asyncio.to_thread(_put)

    async def get_object(self, object_key: str) -> BytesIO:
        def _get():
            response = self.client.get_object(self.bucket_name, object_key)
            try:
                data = BytesIO(response.read())
                return data
            finally:
                response.close()
                response.release_conn()
        return await asyncio.to_thread(_get)

    async def remove_object(self, object_key: str) -> None:
        def _remove():
            self.client.remove_object(self.bucket_name, object_key)
        await asyncio.to_thread(_remove)

    async def copy_object(self, source_key: str, dest_key: str) -> None:
        from minio.commonconfig import CopySource
        def _copy():
            self.client.copy_object(
                bucket_name=self.bucket_name,
                object_name=dest_key,
                source=CopySource(self.bucket_name, source_key)
            )
        await asyncio.to_thread(_copy)

minio_client = MinioClient()
