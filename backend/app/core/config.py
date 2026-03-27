"""Application configuration using Pydantic settings."""
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings

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
    
    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@clm.com"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Security
    WEBHOOK_SECRET: str = "your-webhook-secret"
    
    class Config:
        env_file = str(_env_file)
        case_sensitive = True
        extra = "ignore"


settings = Settings()
