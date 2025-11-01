from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_token, get_current_user
from app.models.user import User, UserRole
from app.models.vendor import Vendor
from app.models.customer import Customer
from app.schemas.auth import Token, UserRegister, UserLogin
from app.schemas.user import UserResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.user import UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    User registration endpoint.
    """
    # password validation
    if user_data.password != user_data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords don't match"
        )
    # TODO: maybe add password strength check later
    # had a bug where weak passwords were accepted - fixed for now
    
    # Check if user already exists
    # Tried using unique constraint on DB but this gives better error message
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    # Could check separately for username vs email but this is simpler
    
    # Find vendor if provided
    vendor = None
    if user_data.vendor_id:
        vendor = db.query(Vendor).filter(Vendor.id == user_data.vendor_id).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid vendor ID"
            )
    elif user_data.domain:
        vendor = db.query(Vendor).filter(Vendor.domain == user_data.domain).first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor not found for this domain"
            )
    
    # create user - hash password first
    hashed_password = User.hash_password(user_data.password)
    # print(f"Creating user: {user_data.username}")  # debug line - remove later
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,  # storing hashed, not plain
        role=user_data.role,
        phone_number=user_data.phone_number,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        vendor_id=vendor.id if vendor else None  # None for superusers
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # TODO: email notification? maybe later
    
    # Create customer profile if role is CUSTOMER
    # Originally did this in a signal but doing it here for cleaner separation
    if user.role == UserRole.CUSTOMER and vendor:
        customer = Customer(
            vendor_id=vendor.id,
            user_id=user.id,
            full_name=f"{user.first_name} {user.last_name}".strip() or user.username,
            email=user.email,
            phone_number=user.phone_number or ""
        )
        db.add(customer)
        db.commit()
    
    return user


class LoginForm(BaseModel):
    """Login form model."""
    username: str
    password: str


@router.post("/login", response_model=Token)
async def login(form_data: LoginForm, db: Session = Depends(get_db)):
    """
    User login endpoint.
    
    Returns JWT tokens with tenant_id and role.
    """
    # Find user
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # build token payload
    token_data = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value if isinstance(user.role, UserRole) else user.role,  # handle enum
    }
    if user.vendor_id:
        token_data["tenant_id"] = user.vendor_id
        vendor = db.query(Vendor).filter(Vendor.id == user.vendor_id).first()
        if vendor:
            token_data["vendor_name"] = vendor.store_name  # useful for frontend
    
    # Create tokens
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

