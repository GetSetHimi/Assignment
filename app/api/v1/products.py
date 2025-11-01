from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.core.dependencies import require_staff, check_tenant_access
from app.models.user import User
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter()


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List products for current tenant.
    """
    if not current_user.vendor_id:
        return []
    
    query = db.query(Product).filter(Product.vendor_id == current_user.vendor_id)
    
    # search
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )
    
    # filter by active
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    products = query.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()
    return products


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff)
):
    """
    Create a new product.
    
    Auto-sets vendor from current user.
    """
    if not current_user.vendor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be associated with a vendor"
        )
    
    # auto assign vendor - important!
    product = Product(
        **product_data.model_dump(),
        vendor_id=current_user.vendor_id,
        created_by_id=current_user.id
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get product details"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # tenant check
    if not check_tenant_access(product, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return product


@router.put("/{product_id}", response_model=ProductResponse)
@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff)
):
    """
    Update product.
    
    Only staff can update.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check tenant access
    if not check_tenant_access(product, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff)
):
    """
    Delete product.
    
    Only store owners can delete - staff cannot.
    Tried putting require_store_owner in dependencies but had to do it here
    because require_staff includes owners but we want only owners for delete.
    """
    from app.core.dependencies import require_store_owner
    require_store_owner(current_user)
    # TODO: Soft delete instead? Keep products but mark as deleted?
    # TODO: Check if product has orders before allowing delete
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check tenant access
    if not check_tenant_access(product, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(product)
    db.commit()
    return None


@router.patch("/{product_id}/update_stock", response_model=ProductResponse)
async def update_stock(
    product_id: int,
    quantity: int = Query(..., ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff)
):
    """
    Update product stock.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check tenant access
    if not check_tenant_access(product, current_user):
        raise HTTPException(status_code=403, detail="Access denied")
    
    product.stock_quantity = quantity
    db.commit()
    db.refresh(product)
    return product

