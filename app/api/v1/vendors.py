
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.vendor import Vendor
from app.schemas.vendor import VendorResponse

router = APIRouter()


@router.get("/", response_model=List[VendorResponse])
async def list_vendors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """list vendors - public endpoint"""
    vendors = db.query(Vendor).filter(Vendor.is_active == True).offset(skip).limit(limit).all()
    return vendors


@router.get("/{domain}", response_model=VendorResponse)
async def get_vendor_by_domain(domain: str, db: Session = Depends(get_db)):
    """get vendor by domain"""
    vendor = db.query(Vendor).filter(Vendor.domain == domain, Vendor.is_active == True).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

