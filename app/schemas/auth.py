"""
Authentication schemas.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[int] = None
    tenant_id: Optional[int] = None
    role: Optional[UserRole] = None
    username: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    username: str
    password: str


class UserRegister(BaseModel):
    """User registration request."""
    username: str
    email: EmailStr
    password: str
    password_confirm: str
    role: UserRole = UserRole.CUSTOMER
    phone_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    vendor_id: Optional[int] = None
    domain: Optional[str] = None


# Import UserResponse here to avoid circular imports
from app.schemas.user import UserResponse


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

