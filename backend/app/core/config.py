"""Application configuration using Pydantic settings."""
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
import secrets

# Resolve .env: check backend/.env first, then project root .env
_this_dir = Path(__file__).resolve().parent          # app/core/
_backend_dir = _this_dir.parent.parent               # backend/
_project_root = _backend_dir.parent                  # CLM/

_env_file = _backend_dir / ".env"
if not _env_file.exists():
    _env_file = _project_root / ".env"


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Basic
    PROJECT_NAME: str = "CLM Platform"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./clm_data.db"

    # JWT — generate a random key if not provided
    SECRET_KEY: str = secrets.token_hex(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@clm.com"

    # CORS — restrictive defaults
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    # Security
    WEBHOOK_SECRET: str = secrets.token_hex(16)

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_API: str = "100/minute"

    # Account lockout
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 30

    # Password policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # Registration
    REGISTRATION_REQUIRES_APPROVAL: bool = True
    ALLOWED_EMAIL_DOMAINS: List[str] = []  # empty = allow all domains

    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx", ".doc", ".xlsx", ".png", ".jpg"]
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = str(_env_file)
        case_sensitive = True
        extra = "ignore"


settings = Settings()
