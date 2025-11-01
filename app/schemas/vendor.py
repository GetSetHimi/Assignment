"""
Vendor schemas.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class VendorBase(BaseModel):
    """Base vendor schema."""
    store_name: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    domain: str
    subdomain: Optional[str] = None
    is_active: bool = True


class VendorCreate(VendorBase):
    """Vendor creation schema."""
    pass


class VendorResponse(VendorBase):
    """Vendor response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Vendor(VendorResponse):
    """Full vendor schema."""
    pass

