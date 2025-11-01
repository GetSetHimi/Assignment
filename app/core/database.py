"""
Database configuration.

SQLAlchemy ORM setup with connection pooling.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from app.core.config import settings

# SQLAlchemy setup
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

# MongoDB setup
mongodb_client: AsyncIOMotorClient = None
mongodb_sync_client: MongoClient = None


def connect_mongodb():
    """
    Create MongoDB connection on application startup.
    """
    global mongodb_client, mongodb_sync_client
    
    if settings.MONGODB_URL:
        try:
            mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
            mongodb_sync_client = MongoClient(settings.MONGODB_URL)
            # Test the connection
            mongodb_sync_client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            mongodb_client = None
            mongodb_sync_client = None
    else:
        print("⚠️  MONGODB_URL not set in .env, MongoDB connection skipped")


def close_mongodb():
    """
    Close MongoDB connection on application shutdown.
    """
    global mongodb_client, mongodb_sync_client
    
    if mongodb_client:
        mongodb_client.close()
    if mongodb_sync_client:
        mongodb_sync_client.close()
    print("MongoDB connection closed")


def get_db():
    """
    Dependency to get SQLAlchemy database session.
    
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


async def get_mongodb():
    """
    Dependency to get MongoDB database instance (async).
    
    Yields the database instance for MongoDB operations.
    """
    if not mongodb_client:
        raise Exception("MongoDB client not initialized. Check MONGODB_URL in .env")
    
    db = mongodb_client[settings.MONGODB_DB_NAME]
    yield db


def get_mongodb_sync():
    """
    Dependency to get MongoDB database instance (sync).
    
    Yields the database instance for synchronous MongoDB operations.
    """
    if not mongodb_sync_client:
        raise Exception("MongoDB client not initialized. Check MONGODB_URL in .env")
    
    db = mongodb_sync_client[settings.MONGODB_DB_NAME]
    yield db

