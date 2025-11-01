"""
Order routes.

Most complex router - handles different permissions for different roles.
Considered separate routers per role but this keeps code DRY.

Had to think through the staff assignment logic carefully.
Tried using separate endpoints but keeping it in one router is cleaner.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from decimal import Decimal
import uuid
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.dependencies import require_staff, require_store_owner, check_tenant_access
from app.models.user import User, UserRole
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.customer import Customer
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderItemCreate

router = APIRouter()


@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List orders for current tenant.
    
    Complex filtering by role.
    """
    if not current_user.vendor_id:
        return []
    
    query = db.query(Order).filter(Order.vendor_id == current_user.vendor_id)
    
    # Customers can only see their own orders
    if current_user.role == UserRole.CUSTOMER:
        customer = db.query(Customer).filter(
            Customer.user_id == current_user.id,
            Customer.vendor_id == current_user.vendor_id
        ).first()
        if customer:
            query = query.filter(Order.customer_id == customer.id)
        else:
            return []
    
    # Staff can see assigned orders and unassigned orders
    elif current_user.role == UserRole.STAFF:
        query = query.filter(
            or_(
                Order.assigned_staff_id == current_user.id,
                Order.assigned_staff_id.is_(None)
            )
        )
    
    # Filter by status
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create order (place order).
    
    Handles nested items and stock updates.
    """
    if not current_user.vendor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a vendor"
        )
    
    # Get or create customer
    customer = db.query(Customer).filter(
        Customer.vendor_id == current_user.vendor_id,
        Customer.user_id == current_user.id
    ).first()
    
    if not customer:
        customer = Customer(
            vendor_id=current_user.vendor_id,
            user_id=current_user.id,
            full_name=f"{current_user.first_name} {current_user.last_name}".strip() or current_user.username,
            email=current_user.email,
            phone_number=current_user.phone_number or ""
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    
    # Generate order number
    # Tried sequential numbers but UUID is safer for concurrent orders
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    # TODO: Check for uniqueness (very unlikely but technically possible)
    
    # Create order first - then we can add items
    # Tried doing this in a transaction but not needed yet
    order = Order(
        vendor_id=current_user.vendor_id,
        customer_id=customer.id,
        order_number=order_number,
        status=order_data.status,
        shipping_address=order_data.shipping_address,
        notes=order_data.notes
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Calculate total and create items
    total_amount = Decimal('0.00')
    for item_data in order_data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            db.delete(order)
            db.commit()
            raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")
        
        # vendor check - security
        if product.vendor_id != current_user.vendor_id:
            db.delete(order)
            db.commit()
            raise HTTPException(
                status_code=403,
                detail=f"Product {product.name} does not belong to this vendor"
            )
        
        # active check
        if not product.is_active:
            db.delete(order)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Product {product.name} is not active"
            )
        
        # stock check
        if product.stock_quantity < item_data.quantity:
            db.delete(order)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}"
            )
        
        # update stock
        product.stock_quantity -= item_data.quantity
        # TODO: race condition possible here - fix with atomic update later
        db.add(product)
        
        # create order item
        subtotal = item_data.unit_price * item_data.quantity
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,  # snapshot price
            subtotal=subtotal
        )
        db.add(order_item)
        total_amount += subtotal
    
    # set total
    order.total_amount = total_amount
    db.commit()
    db.refresh(order)
    
    return order


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get order details."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check tenant access
    if not check_tenant_access(order, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Customers can only see their own orders
    if current_user.role == UserRole.CUSTOMER:
        customer = db.query(Customer).filter(
            Customer.user_id == current_user.id,
            Customer.vendor_id == current_user.vendor_id
        ).first()
        if not customer or order.customer_id != customer.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return order


@router.put("/{order_id}", response_model=OrderResponse)
@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff)
):
    """
    Update order.
    
    Staff can only update assigned orders or unassigned orders.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check tenant access
    if not check_tenant_access(order, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Staff can only update assigned orders or unassigned
    if current_user.role == UserRole.STAFF:
        if order.assigned_staff_id and order.assigned_staff_id != current_user.id:
            raise HTTPException(status_code=403, detail="Order is assigned to another staff member")
    
    # Update fields
    update_data = order_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_owner)
):
    """
    Delete order.
    
    Only store owners can delete orders.
    Tried soft delete but hard delete is simpler for MVP.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check tenant access
    if not check_tenant_access(order, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # TODO: Prevent deletion if order is already delivered?
    # if order.status == OrderStatus.DELIVERED:
    #     raise HTTPException(...)
    
    db.delete(order)
    db.commit()
    # TODO: Log deletion? Send notification?
    return None


@router.patch("/{order_id}/update_status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff)
):
    """
    Update order status.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check tenant access
    if not check_tenant_access(order, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Staff can only update assigned orders
    # Tried using permission dependency but this is more explicit
    if current_user.role == UserRole.STAFF:
        if order.assigned_staff_id and order.assigned_staff_id != current_user.id:
            raise HTTPException(status_code=403, detail="Order is assigned to another staff member")
    
    # Validate status - could add transition rules here
    # e.g., can only cancel pending orders, can't go backwards, etc.
    new_status = status_data.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    try:
        order.status = OrderStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
    # TODO: Add status transition validation
    # old_status = order.status
    # if not self._can_transition_to(old_status, new_status):
    #     raise HTTPException(...)
    
    # TODO: Send email notification on status change?
    # send_order_status_email.delay(order.id, old_status, new_status)
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/assign_staff", response_model=OrderResponse)
async def assign_staff(
    order_id: int,
    assign_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_store_owner)
):
    """
    Assign order to staff member.
    
    Only store owners can assign orders.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check tenant access
    if not check_tenant_access(order, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    staff_id = assign_data.get("staff_id")
    if staff_id:
        staff = db.query(User).filter(
            User.id == staff_id,
            User.vendor_id == current_user.vendor_id,
            User.role == UserRole.STAFF
        ).first()
        if not staff:
            raise HTTPException(status_code=404, detail="Staff member not found")
        order.assigned_staff_id = staff_id
    else:
        order.assigned_staff_id = None
    
    db.commit()
    db.refresh(order)
    return order


@router.get("/my-orders", response_model=List[OrderResponse])
async def my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's orders.
    
    For customers to view their own orders.
    """
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for customers only"
        )
    
    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id,
        Customer.vendor_id == current_user.vendor_id
    ).first()
    
    if not customer:
        return []
    
    orders = db.query(Order).filter(Order.customer_id == customer.id).order_by(Order.created_at.desc()).all()
    return orders

