"""
User schemas.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
from app.schemas.vendor import VendorResponse


class UserBase(BaseModel):
    """Base user schema."""
    username: str
    email: EmailStr
    role: UserRole
    phone_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """User creation schema."""
    password: str


class UserResponse(UserBase):
    """User response schema."""
    id: int
    vendor: Optional[VendorResponse] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class User(UserResponse):
    """Full user schema."""
    pass

