
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
  
    # App settings
    PROJECT_NAME: str = "Multi-Tenant E-Commerce Platform"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    # TODO: Add environment-based settings (dev/staging/prod)
    
    # Database
    DATABASE_URL: str = "sqlite:///./ecommerce.db"
    # TODO: Switch to PostgreSQL in production
    # DATABASE_URL: str = "postgresql://user:pass@localhost/dbname"
    
    # MongoDB
    MONGODB_URL: str = ""
    MONGODB_DB_NAME: str = "ecommerce"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    # TODO: Generate random secret key in production
    # import secrets; secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    # Tried shorter expiry but frontend team asked for longer
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    # TODO: Restrict CORS in production - allow only frontend domain
    # CORS_ORIGINS: list = ["https://yourdomain.com"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

