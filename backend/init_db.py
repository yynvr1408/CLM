"""Database initialization script."""

from sqlalchemy import text

from app.database.session import engine
from app.models.models import Base


def reset_schema():
    """Drop and recreate public schema."""

    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO clm_user"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))


def create_tables():
    """Create database tables."""

    Base.metadata.create_all(bind=engine)


def init_db():
    """Initialize database."""

    print("Resetting database schema...")
    reset_schema()

    print("Creating tables...")
    create_tables()

    print("Database initialization complete.")


if __name__ == "__main__":
    init_db()