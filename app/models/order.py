
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from decimal import Decimal
from app.core.database import Base


class OrderStatus(str, enum.Enum):
    """Order status enum."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Order(Base):
    """
    Order model, tenant-specific.
    
    Tried calculating total_amount in a property first, but storing it makes queries faster.
    Using separate OrderItem model for line items - considered JSONField but FK is better
    for queries and relationships.
    """
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    # Tried UUIDField but string with prefix is more readable in admin
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    # TODO: Check for uniqueness on insert (very unlikely collision but still)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    # Calculate this when order is created/updated - see order creation route
    # Tried using @property but storing it makes queries faster
    total_amount = Column(Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    # Storing shipping address separately in case customer moves
    shipping_address = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    # For staff assignment - originally thought about ManyToMany but one staff per order is simpler
    assigned_staff_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    assigned_staff = relationship("User", back_populates="assigned_orders", foreign_keys=[assigned_staff_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status.value}')>"


class OrderItem(Base):
    """
    Order items model.
    
    Storing unit_price separately because product price might change later,
    but we want to preserve the price at time of order.
    """
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    # Snapshot of price at time of order - product.price might change
    # Important! Product price might go up/down but we keep original price
    unit_price = Column(Numeric(10, 2), nullable=False)
    # Could calculate this on the fly, but storing it makes aggregations faster
    # Tried calculating in @property but this is better for queries
    subtotal = Column(Numeric(10, 2), nullable=False)
    # TODO: Could add discount_amount field for promotions?
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"

