
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.dependencies import require_store_owner
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_owner)
):
    """
    List users for current tenant.
    
    Only store owners can access.
    """
    if not current_user.vendor_id:
        return []
    
    users = db.query(User).filter(
        User.vendor_id == current_user.vendor_id
    ).offset(skip).limit(limit).all()
    
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_owner)
):
    """
    Create a new user.
    
    Only store owners can create users.
    """
    if not current_user.vendor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a vendor"
        )
    
    # check existing
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # create user
    hashed_password = User.hash_password(user_data.password if hasattr(user_data, 'password') else "default123")
    user = User(
        **user_data.model_dump(exclude={'password'}),
        hashed_password=hashed_password,
        vendor_id=current_user.vendor_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_owner)
):
    """get user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # tenant check
    if user.vendor_id != current_user.vendor_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return user

