"""
Customer schemas.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.schemas.vendor import VendorResponse
from app.schemas.user import UserResponse


class CustomerBase(BaseModel):
    """Base customer schema."""
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Customer creation schema."""
    pass


class CustomerResponse(CustomerBase):
    """Customer response schema."""
    id: int
    vendor: Optional[VendorResponse] = None
    user: Optional[UserResponse] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Customer(CustomerResponse):
    """Full customer schema."""
    pass

