from fastapi import APIRouter
from app.api.v1 import auth, vendors, products, orders, customers, users

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

