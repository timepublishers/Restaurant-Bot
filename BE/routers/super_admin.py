from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from database.main_db import get_main_db
from controllers.super_admin_controller import SuperAdminController
from schemas.restaurant_schemas import RestaurantCreate, RestaurantUpdate, RestaurantResponse, RestaurantListResponse
from utils.auth import verify_token

router = APIRouter()
security = HTTPBearer()

def verify_super_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify super admin authentication"""
    payload = verify_token(credentials.credentials)
    if payload.get("user_type") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return payload

@router.post("/restaurants", response_model=RestaurantResponse)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    db: Session = Depends(get_main_db),
    current_admin = Depends(verify_super_admin)
):
    """Create a new restaurant"""
    return SuperAdminController.create_restaurant(restaurant_data, db)

@router.get("/restaurants", response_model=RestaurantListResponse)
async def get_restaurants(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_main_db),
    current_admin = Depends(verify_super_admin)
):
    """Get list of restaurants with pagination"""
    return SuperAdminController.get_restaurants(db, page, limit, search)

@router.get("/restaurants/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(
    restaurant_id: str,
    db: Session = Depends(get_main_db),
    current_admin = Depends(verify_super_admin)
):
    """Get restaurant by ID"""
    return SuperAdminController.get_restaurant(restaurant_id, db)

@router.put("/restaurants/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: str,
    update_data: RestaurantUpdate,
    db: Session = Depends(get_main_db),
    current_admin = Depends(verify_super_admin)
):
    """Update restaurant details"""
    return SuperAdminController.update_restaurant(restaurant_id, update_data, db)

@router.delete("/restaurants/{restaurant_id}")
async def delete_restaurant(
    restaurant_id: str,
    db: Session = Depends(get_main_db),
    current_admin = Depends(verify_super_admin)
):
    """Delete restaurant"""
    return SuperAdminController.delete_restaurant(restaurant_id, db)