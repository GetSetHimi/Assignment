"""
FastAPI main application.

Multi-tenant e-commerce platform with FastAPI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import engine, Base, connect_mongodb, close_mongodb
from app.api.v1 import api_router
from app.models import Vendor, User, Product, Customer, Order, OrderItem  # Import models to register them


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    # Create all database tables
    # In production, use Alembic migrations instead
    # TODO: Set up Alembic for proper migrations
    Base.metadata.create_all(bind=engine)
    # Note: This creates tables on startup - fine for dev but use migrations in prod
    
    # Connect to MongoDB
    connect_mongodb()
    
    yield
    
    # Shutdown
    close_mongodb()

app = FastAPI(
    title="Multi-Tenant E-Commerce Platform",
    description="Multi-tenant e-commerce backend with FastAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount static and media files (for development)
# In production, use nginx or CDN
# Tried using separate routers for these but mounting is simpler
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")
# TODO: Add file size limits and validation for media uploads
# TODO: Consider using S3 or similar for media storage in production


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Multi-Tenant E-Commerce Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

