"""Database session configuration."""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Build engine kwargs based on database type
_is_sqlite = "sqlite" in settings.DATABASE_URL
_engine_kwargs: dict = {
    "echo": settings.DEBUG,
}
if _is_sqlite:
    # This block is removed as connect_args is handled separately below
    pass
else:
    _engine_kwargs["pool_pre_ping"] = True

# Create database engine
engine_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **engine_args, **_engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
