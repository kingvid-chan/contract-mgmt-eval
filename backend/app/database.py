"""Database engine, session, and declarative base."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine

from app.config import settings


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key support for SQLite on every connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yield a database session and close it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_migrations():
    """Run idempotent schema migrations for SQLite.

    Checks for missing columns and adds them safely.
    Extend this function for future schema changes.
    """
    import sqlalchemy

    with engine.connect() as conn:
        # Migration 0.0.2: add ip_address column to audit_logs
        result = conn.execute(
            sqlalchemy.text(
                "SELECT COUNT(*) FROM pragma_table_info('audit_logs') WHERE name='ip_address'"
            )
        )
        row = result.fetchone()
        if row and row[0] == 0:
            conn.execute(
                sqlalchemy.text(
                    "ALTER TABLE audit_logs ADD COLUMN ip_address VARCHAR(45)"
                )
            )
            conn.commit()


def init_db():
    """Create all tables and run migrations. Called on application startup."""
    _run_migrations()
    Base.metadata.create_all(bind=engine)
