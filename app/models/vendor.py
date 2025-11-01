"""
Vendor/Tenant model for multi-tenancy.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Vendor(Base):
    """
    Vendor/Tenant model for multi-tenancy.
    
    Originally thought about using a separate Tenant model, but decided Vendor itself
    can act as the tenant since each vendor has their own store.
    Tried adding a slug field for URL routing but decided domain is enough for now.
    """
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), unique=True, nullable=False, index=True)
    contact_phone = Column(String(20), nullable=True)
    # Using domain for tenant identification - could also use subdomain routing later
    domain = Column(String(255), unique=True, nullable=False, index=True)
    # TODO: Add domain validation (must be valid domain format)
    subdomain = Column(String(255), unique=True, nullable=True)
    # Tried making subdomain required but domain is enough for MVP
    is_active = Column(Boolean, default=True, nullable=False)
    # TODO: Maybe add created_by field to track who created the vendor?
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="vendor", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="vendor", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="vendor", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="vendor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vendor(id={self.id}, store_name='{self.store_name}')>"

