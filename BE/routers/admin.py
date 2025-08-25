from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, func
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database.tenant_db import TenantDatabase, Order, OrderItem, MenuItem, Session as ChatSession, Message, Settings, OrderStatus, PaymentStatus
from database.main_db import Restaurant, get_main_db
from utils.auth import verify_token

router = APIRouter()
security = HTTPBearer()

def get_tenant_db_by_token(credentials: HTTPAuthorizationCredentials, main_db: Session) -> TenantDatabase:
    """Get tenant database from JWT token"""
    payload = verify_token(credentials.credentials)
    restaurant_id = payload.get("sub")
    
    restaurant = main_db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    from database.tenant_db import get_tenant_db
    db_config = {
        'db_host': restaurant.db_host,
        'db_port': restaurant.db_port,
        'db_name': restaurant.db_name,
        'db_user': restaurant.db_user,
        'db_password': restaurant.db_password
    }
    
    return get_tenant_db(db_config)
class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None

class SessionUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None

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
    
    # Verify admin authentication
    tenant_db = get_tenant_db_by_token(credentials, main_db)
    
    db = tenant_db.get_session()
    try:
        query = db.query(Order)
        
        # Apply filters
        if status:
            query = query.filter(Order.status == OrderStatus(status))
        if payment_status:
            query = query.filter(Order.payment_status == PaymentStatus(payment_status))
        if date_from:
            query = query.filter(Order.created_at >= date_from)
        if date_to:
            query = query.filter(Order.created_at <= date_to)
        
        # Apply search (search in session customer details)
        if search:
            query = query.join(ChatSession).filter(
                func.concat(
                    func.coalesce(ChatSession.customer_name, ''),
                    ' ',
                    func.coalesce(ChatSession.customer_phone, ''),
                    ' ',
                    func.coalesce(ChatSession.customer_email, '')
                ).ilike(f"%{search}%")
            )
        
        # Apply sorting
        sort_column = getattr(Order, sort_by, Order.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        orders = query.offset((page - 1) * limit).limit(limit).all()
        
        # Format response
        orders_data = []
        for order in orders:
            # Get session info
            session = db.query(ChatSession).filter(ChatSession.id == order.session_id).first()
            
            # Get order items
            items = db.query(OrderItem, MenuItem).join(MenuItem).filter(
                OrderItem.order_id == order.id
            ).all()
            
            orders_data.append({
                "id": str(order.id),
                "status": order.status.value,
                "payment_status": order.payment_status.value,
                "total_price": float(order.total_price),
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat(),
                "payment_proof_text": order.payment_proof_text,
                "payment_proof_image_url": order.payment_proof_image_url,
                "customer": {
                    "name": session.customer_name if session else None,
                    "phone": session.customer_phone if session else None,
                    "email": session.customer_email if session else None,
                    "address": session.delivery_address if session else None,
                    "notes": session.notes if session else None
                },
                "items": [{
                    "id": str(item.OrderItem.id),
                    "name": item.MenuItem.name,
                    "quantity": item.OrderItem.quantity,
                    "unit_price": float(item.OrderItem.unit_price),
                    "line_total": float(item.OrderItem.quantity * item.OrderItem.unit_price)
                } for item in items]
            })
        
        return {
            "orders": orders_data,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
        
    finally:
        db.close()

@router.get("/orders/{order_id}")
async def get_order_detail(
    order_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Get detailed order information"""
    
    tenant_db = get_tenant_db_by_token(credentials, main_db)
    
    db = tenant_db.get_session()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get session and items (same logic as above)
        session = db.query(ChatSession).filter(ChatSession.id == order.session_id).first()
        items = db.query(OrderItem, MenuItem).join(MenuItem).filter(
            OrderItem.order_id == order.id
        ).all()
        
        return {
            "id": str(order.id),
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "total_price": float(order.total_price),
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "payment_proof_text": order.payment_proof_text,
            "payment_proof_image_url": order.payment_proof_image_url,
            "customer": {
                "name": session.customer_name if session else None,
                "phone": session.customer_phone if session else None,
                "email": session.customer_email if session else None,
                "address": session.delivery_address if session else None,
                "notes": session.notes if session else None
            },
            "items": [{
                "id": str(item.OrderItem.id),
                "name": item.MenuItem.name,
                "description": item.MenuItem.description,
                "quantity": item.OrderItem.quantity,
                "unit_price": float(item.OrderItem.unit_price),
                "line_total": float(item.OrderItem.quantity * item.OrderItem.unit_price)
            } for item in items]
        }
        
    finally:
        db.close()

@router.put("/orders/{order_id}")
async def update_order(
    order_id: str,
    update_data: OrderUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Update order status or payment status"""
    
    tenant_db = get_tenant_db_by_token(credentials, main_db)
    
    db = tenant_db.get_session()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update fields
        if update_data.status:
            order.status = OrderStatus(update_data.status)
        if update_data.payment_status:
            order.payment_status = PaymentStatus(update_data.payment_status)
        
        order.updated_at = datetime.utcnow()
        db.commit()
        
        # If marking as paid and confirmed, send bot message
        if (update_data.payment_status == "paid" and 
            update_data.status == "confirmed"):
            
            bot_message = Message(
                session_id=order.session_id,
                sender="bot",
                content="Your order has been confirmed! We'll start preparing it shortly."
            )
            db.add(bot_message)
            db.commit()
        
        return {"message": "Order updated successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@router.get("/metrics/24h")
async def get_24h_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Get 24-hour rolling metrics"""
    
    tenant_db = get_tenant_db_by_token(credentials, main_db)
    
    db = tenant_db.get_session()
    try:
        now = datetime.utcnow()
        yesterday = now - timedelta(hours=24)
        
        # Revenue (paid orders last 24h)
        revenue_result = db.query(func.coalesce(func.sum(Order.total_price), 0)).filter(
            and_(
                Order.payment_status == PaymentStatus.paid,
                Order.created_at >= yesterday
            )
        ).scalar()
        
        # Delivered orders last 24h
        delivered_count = db.query(func.count(Order.id)).filter(
            and_(
                Order.status == OrderStatus.delivered,
                Order.updated_at >= yesterday
            )
        ).scalar()
        
        # Total orders last 24h
        total_orders = db.query(func.count(Order.id)).filter(
            Order.created_at >= yesterday
        ).scalar()
        
        # Pending orders (current)
        pending_orders = db.query(func.count(Order.id)).filter(
            Order.status.in_([OrderStatus.pending, OrderStatus.confirmed, OrderStatus.in_process])
        ).scalar()
        
        return {
            "revenue_24h": float(revenue_result or 0),
            "delivered_24h": delivered_count or 0,
            "total_orders_24h": total_orders or 0,
            "pending_orders": pending_orders or 0
        }
        
    finally:
        db.close()

@router.put("/sessions/{session_id}")
async def update_session(
    session_id: str,
    update_data: SessionUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    main_db: Session = Depends(get_main_db)
):
    """Update session/customer details"""
    
    tenant_db = get_tenant_db_by_token(credentials, main_db)
    
    db = tenant_db.get_session()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(session, field, value)
        
        session.updated_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Session updated successfully"}
        
    finally:
        db.close()