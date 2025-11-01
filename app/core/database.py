"""
Database configuration.

SQLAlchemy ORM setup with connection pooling.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine
# Tried async SQLAlchemy but keeping sync for simplicity - can upgrade later
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    # SQLite needs check_same_thread=False for FastAPI
    # PostgreSQL/MySQL don't need this
)
# TODO: Add connection pooling settings for production
# pool_size=10, max_overflow=20, pool_pre_ping=True

# Create session factory
# autocommit=False because we want to control transactions manually
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# TODO: Consider using async sessionmaker for async operations

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session.
    
    This yields the session and closes it automatically.
    Using generator function (yield) so FastAPI can handle session lifecycle.
    
    Note: Commit is done explicitly in routes, not here.
    Could auto-commit here but explicit commits give better control.
    """
    db = SessionLocal()
    try:
        yield db
        # Commit happens in routes explicitly - don't auto-commit here
        # Tried auto-committing but explicit commits are better for error handling
    except Exception:
        # Rollback on error - important!
        db.rollback()
        raise
    finally:
        db.close()
        # TODO: Could add session pooling here for better performance

