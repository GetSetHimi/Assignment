from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.dependencies import check_tenant_access
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.schemas.customer import CustomerResponse

router = APIRouter()


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List customers for current tenant.
    
    Customers can only see themselves.
    """
    if not current_user.vendor_id:
        return []
    
    query = db.query(Customer).filter(Customer.vendor_id == current_user.vendor_id)
    
    # customer can only see themselves
    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Customer.user_id == current_user.id)
    
    # search
    if search:
        query = query.filter(
            or_(
                Customer.full_name.ilike(f"%{search}%"),
                Customer.email.ilike(f"%{search}%")
            )
        )
    
    customers = query.offset(skip).limit(limit).all()
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get customer details.
    
    Customers can only see themselves - staff/owners can see all.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # customer access check
    if current_user.role == UserRole.CUSTOMER and customer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # tenant check
    if not check_tenant_access(customer, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return customer

