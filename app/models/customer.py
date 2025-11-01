
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Customer(Base):
   
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    # TODO: Add validation for phone number format
    phone_number = Column(String(20), nullable=True)
    # Considered using Address model but keeping it simple for now
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="customers")
    user = relationship("User", back_populates="customer_profiles")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    
    # Unique constraint - ensures same email can exist across vendors but not within same vendor
    # Tried just email unique but that broke multi-tenancy
    __table_args__ = (
        UniqueConstraint('vendor_id', 'email', name='unique_vendor_email'),
    )
    
    def __repr__(self):
        return f"<Customer(id={self.id}, full_name='{self.full_name}', vendor_id={self.vendor_id})>"

