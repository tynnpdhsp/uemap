from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Môi trường
    ENV: str = "dev"

    # MongoDB
    MONGODB_URI: str = "mongodb://mongodb:27017"
    MONGODB_DB_NAME: str = "ban_do_sv_sp"

    # MinIO
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "ban-do-uploads"
    MINIO_USE_SSL: bool = False

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 ngày (sinh viên)
    JWT_ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 giờ (quản trị)

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "Ban do sinh vien su pham"
    SMTP_FROM_EMAIL: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Bản đồ mặc định
    MAP_DEFAULT_CENTER_LAT: float = 10.7628
    MAP_DEFAULT_CENTER_LNG: float = 106.6824
    MAP_DEFAULT_ZOOM: int = 15

    class Config:
        env_file = "../.env"
        case_sensitive = True


settings = Settings()
