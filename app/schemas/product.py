"""
Product schemas.

Using Pydantic for type-safe validation.
Considered nested schemas but separate schemas are cleaner.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.schemas.vendor import VendorResponse


class ProductBase(BaseModel):
    """
    Base product schema.
    
    Common fields for create/update/response.
    Tried separate schemas for each but this reduces duplication.
    """
    name: str
    description: Optional[str] = None
    price: Decimal  # Using Decimal instead of float for money - important!
    stock_quantity: int = 0
    image: Optional[str] = None  # TODO: Add image upload validation
    is_active: bool = True


class ProductCreate(ProductBase):
    """Product creation schema."""
    pass


class ProductUpdate(BaseModel):
    """
    Product update schema.
    
    All fields optional for partial updates.
    Could use PATCH vs PUT distinction but this works for both.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    # TODO: Add validation - stock can't be negative?
    image: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Product response schema."""
    id: int
    vendor: Optional[VendorResponse] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Product(ProductResponse):
    """Full product schema."""
    pass

