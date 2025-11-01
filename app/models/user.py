"""
User model with tenant and role support.

Password hashing using passlib with bcrypt.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from passlib.context import CryptContext
from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enum."""
    STORE_OWNER = "STORE_OWNER"
    STAFF = "STAFF"
    CUSTOMER = "CUSTOMER"


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """
    Custom User model with tenant and role support.
    
    Considered using email as primary identifier but
    username is fine for now.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(150), nullable=True)
    last_name = Column(String(150), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    # Added null=True for superusers who might not belong to a vendor
    # Had some issues with admin access before this - superuser couldn't login!
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    # Tried making phone_number required but caused issues with existing users
    # Considered using regex validation here but keeping it simple for now
    phone_number = Column(String(20), nullable=True)
    # TODO: Add phone number validation in schema layer
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    vendor = relationship("Vendor", back_populates="users")
    created_products = relationship("Product", back_populates="created_by", foreign_keys="Product.created_by_id")
    assigned_orders = relationship("Order", back_populates="assigned_staff", foreign_keys="Order.assigned_staff_id")
    customer_profiles = relationship("Customer", back_populates="user", cascade="all, delete-orphan")
    
    @staticmethod
    def hash_password(password: str) -> str:
        """hash password"""
        return pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """verify password"""
        return pwd_context.verify(password, self.hashed_password)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

