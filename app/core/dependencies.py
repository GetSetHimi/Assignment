from typing import Optional, List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.core.database import get_db
from app.core.security import get_current_active_user


def require_role(required_role: UserRole):
    """
    Dependency factory for role-based access.
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role.value}"
            )
        return current_user
    return role_checker


def require_roles(required_roles: List[UserRole]):
    """
    Dependency factory for multiple roles.
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required one of roles: {[r.value for r in required_roles]}"
            )
        return current_user
    return role_checker


def require_vendor(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency to ensure user has a vendor (tenant).
    """
    if current_user.vendor_id is None and current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a vendor"
        )
    return current_user


def require_store_owner(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency for store owner only."""
    if current_user.role != UserRole.STORE_OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store owner access required"
        )
    return current_user


def require_staff(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency for staff or store owner."""
    if current_user.role not in [UserRole.STORE_OWNER, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff or store owner access required"
        )
    return current_user


def check_tenant_access(obj, current_user: User) -> bool:
    """check if user can access this object"""
    # get vendor id from object
    vendor_id = None
    if hasattr(obj, 'vendor_id'):
        vendor_id = obj.vendor_id
    elif hasattr(obj, 'customer') and hasattr(obj.customer, 'vendor_id'):
        vendor_id = obj.customer.vendor_id
    elif hasattr(obj, 'user') and hasattr(obj.user, 'vendor_id'):
        vendor_id = obj.user.vendor_id
    
    # check match
    if vendor_id and current_user.vendor_id:
        return current_user.vendor_id == vendor_id
    
    return False

