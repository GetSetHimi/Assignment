"""
Order schemas.

This one was tricky - had to handle nested items, stock updates, calculations.
Tried using nested schemas with create() but separate schemas give more control.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.order import OrderStatus
from app.schemas.vendor import VendorResponse
from app.schemas.customer import CustomerResponse
from app.schemas.product import ProductResponse


class OrderItemBase(BaseModel):
    """Base order item schema."""
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderItemCreate(OrderItemBase):
    """Order item creation schema."""
    pass


class OrderItemResponse(OrderItemBase):
    """Order item response schema."""
    id: int
    product_name: Optional[str] = None
    subtotal: Decimal
    
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Base order schema."""
    shipping_address: str
    notes: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING


class OrderCreate(OrderBase):
    """Order creation schema."""
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    """Order update schema."""
    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    assigned_staff_id: Optional[int] = None


class OrderResponse(OrderBase):
    """Order response schema."""
    id: int
    order_number: str
    vendor: Optional[VendorResponse] = None
    customer: Optional[CustomerResponse] = None
    total_amount: Decimal
    assigned_staff_username: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Order(OrderResponse):
    """Full order schema."""
    pass

