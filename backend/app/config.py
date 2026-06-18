"""Application configuration."""

import os


class Settings:
    SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "contract-mgmt-eval-dev-secret-key-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'contract_mgmt.db')}",
    )

    UPLOAD_DIR: str = os.environ.get(
        "UPLOAD_DIR",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"),
    )
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    ALLOWED_EXTENSIONS: set = {".pdf", ".doc", ".docx"}
    ALLOWED_MIME_TYPES: set = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    CORS_ORIGINS: list = ["*"]

    BASE_PATH: str = "/projects/contract-mgmt-eval"


settings = Settings()
