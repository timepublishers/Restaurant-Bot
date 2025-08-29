from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database.main_db import get_main_db
from controllers.admin_controller import AdminController
from schemas.admin_schemas import OrderUpdate, SessionUpdate, MenuItemCreate, MenuItemUpdate, MenuCreate, MenuUpdate

router = APIRouter()
security = HTTPBearer()

@router.get("/orders")
async def get_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Get orders with filtering and pagination"""
    return AdminController.get_orders(
        credentials.credentials, main_db, page, limit, status, payment_status,
        sort_by, sort_order, search, date_from, date_to
    )

@router.get("/orders/{order_id}")
async def get_order_detail(
    order_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Get detailed order information"""
    return AdminController.get_order_detail(credentials.credentials, main_db, order_id)

@router.put("/orders/{order_id}")
async def update_order(
    order_id: str,
    update_data: OrderUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Update order status or payment status"""
    return AdminController.update_order(credentials.credentials, main_db, order_id, update_data)

@router.get("/metrics/24h")
async def get_24h_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Get 24-hour rolling metrics"""
    return AdminController.get_24h_metrics(credentials.credentials, main_db)

@router.put("/sessions/{session_id}")
async def update_session(
    session_id: str,
    update_data: SessionUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Update session/customer details"""
    return AdminController.update_session(credentials.credentials, main_db, session_id, update_data)

@router.get("/menus")
async def get_menus(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Get all menus"""
    return AdminController.get_menus(credentials.credentials, main_db)

@router.post("/menus")
async def create_menu(
    menu_data: MenuCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Create a new menu"""
    return AdminController.create_menu(credentials.credentials, main_db, menu_data)

@router.get("/menu-items")
async def get_menu_items(
    menu_id: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Get menu items"""
    return AdminController.get_menu_items(credentials.credentials, main_db, menu_id)

@router.post("/menus/{menu_id}/items")
async def create_menu_item(
    menu_id: str,
    item_data: MenuItemCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Create a new menu item"""
    return AdminController.create_menu_item(credentials.credentials, main_db, menu_id, item_data)

@router.put("/menu-items/{item_id}")
async def update_menu_item(
    item_id: str,
    item_data: MenuItemUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Update a menu item"""
    return AdminController.update_menu_item(credentials.credentials, main_db, item_id, item_data)

@router.delete("/menu-items/{item_id}")
async def delete_menu_item(
    item_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Delete a menu item"""
    return AdminController.delete_menu_item(credentials.credentials, main_db, item_id)