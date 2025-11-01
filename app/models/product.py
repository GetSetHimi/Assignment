
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from app.core.database import Base


class Product(Base):
    """
    Product model, tenant-specific.
    
    Each product is tied to a vendor - this is the core of multi-tenancy.
    Tried using a GenericForeignKey first but foreign key is simpler and more efficient.
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Used Decimal instead of Float for money - learned this the hard way in another project
    # Float precision issues caused problems with currency calculations!
    price = Column(Numeric(10, 2), nullable=False)
    # TODO: Add low_stock_threshold field for inventory alerts
    # TODO: Add discount_price field for sales?
    stock_quantity = Column(Integer, default=0, nullable=False)
    image = Column(String(255), nullable=True)  # Store file path instead of FileField
    # SQLAlchemy doesn't have ImageField - storing path is simpler
    # TODO: Add image validation (size, format, etc.)
    # TODO: Consider using FileField equivalent or cloud storage
    # Thought about making is_active a status field with choices, but boolean works fine
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="products")
    created_by = relationship("User", back_populates="created_products", foreign_keys=[created_by_id])
    order_items = relationship("OrderItem", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', vendor_id={self.vendor_id})>"

