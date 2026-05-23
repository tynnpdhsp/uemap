from minio import Minio

from app.core.config import settings

minio_client: Minio = None  # type: ignore


def connect_minio():
    global minio_client
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_SSL,
    )

    # Tạo bucket nếu chưa tồn tại
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
        minio_client.make_bucket(settings.MINIO_BUCKET_NAME)


def get_minio() -> Minio:
    return minio_client
