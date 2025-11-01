"""
Pydantic schemas for request/response validation.

Using Pydantic for type-safe validation and serialization.
"""
from app.schemas.auth import Token, TokenData, UserLogin, UserRegister
from app.schemas.user import User, UserCreate, UserResponse
from app.schemas.vendor import Vendor, VendorCreate, VendorResponse
from app.schemas.product import Product, ProductCreate, ProductUpdate, ProductResponse
from app.schemas.customer import Customer, CustomerCreate, CustomerResponse
from app.schemas.order import OrderItemCreate, OrderItemResponse, Order, OrderCreate, OrderUpdate, OrderResponse

__all__ = [
    "Token", "TokenData", "UserLogin", "UserRegister",
    "User", "UserCreate", "UserResponse",
    "Vendor", "VendorCreate", "VendorResponse",
    "Product", "ProductCreate", "ProductUpdate", "ProductResponse",
    "Customer", "CustomerCreate", "CustomerResponse",
    "OrderItemCreate", "OrderItemResponse", "Order", "OrderCreate", "OrderUpdate", "OrderResponse",
]

