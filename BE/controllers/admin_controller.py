from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, func
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime, timedelta

from database.tenant_db import TenantDatabase
from models.tenant_models import Order, OrderItem, MenuItem, Menu, Session as ChatSession, Message, Settings, OrderStatus, PaymentStatus
from models.main_models import Restaurant
from schemas.admin_schemas import OrderUpdate, SessionUpdate, MenuItemCreate, MenuItemUpdate, MenuCreate, MenuUpdate
from utils.auth import verify_token
import json

class AdminController:
    @staticmethod
    def get_tenant_db_by_token(token: str, main_db: Session) -> TenantDatabase:
        """Get tenant database from JWT token"""
        payload = verify_token(token)
        restaurant_id = payload.get("sub")
        
        restaurant = main_db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        from database.tenant_db import get_tenant_db_from_url
        return get_tenant_db_from_url(restaurant.db_url)

    @staticmethod
    def get_orders(
        token: str,
        main_db: Session,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        payment_status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ):
        """Get orders with filtering and pagination"""
        
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
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

    @staticmethod
    def get_order_detail(token: str, main_db: Session, order_id: str):
        """Get detailed order information"""
        
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
        db = tenant_db.get_session()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Get session and items
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

    @staticmethod
    def update_order(token: str, main_db: Session, order_id: str, update_data: OrderUpdate):
        """Update order status or payment status"""
        
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
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

    @staticmethod
    def get_24h_metrics(token: str, main_db: Session):
        """Get 24-hour rolling metrics"""
        
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
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

    @staticmethod
    def update_session(token: str, main_db: Session, session_id: str, update_data: SessionUpdate):
        """Update session/customer details"""
        
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
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

    @staticmethod
    def get_menus(token: str, main_db: Session):
        """Get all menus for the restaurant"""
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
        db = tenant_db.get_session()
        try:
            menus = db.query(Menu).all()
            return [{
                "id": str(menu.id),
                "name": menu.name,
                "description": menu.description,
                "created_at": menu.created_at.isoformat(),
                "updated_at": menu.updated_at.isoformat()
            } for menu in menus]
        finally:
            db.close()

    @staticmethod
    def create_menu(token: str, main_db: Session, menu_data: MenuCreate):
        """Create a new menu"""
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
        db = tenant_db.get_session()
        try:
            menu = Menu(
                name=menu_data.name,
                description=menu_data.description
            )
            db.add(menu)
            db.commit()
            db.refresh(menu)
            
            return {
                "id": str(menu.id),
                "name": menu.name,
                "description": menu.description,
                "created_at": menu.created_at.isoformat(),
                "updated_at": menu.updated_at.isoformat()
            }
        finally:
            db.close()

    @staticmethod
    def get_menu_items(token: str, main_db: Session, menu_id: Optional[str] = None):
        """Get menu items, optionally filtered by menu"""
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
        db = tenant_db.get_session()
        try:
            query = db.query(MenuItem)
            if menu_id:
                query = query.filter(MenuItem.menu_id == menu_id)
            
            items = query.all()
            return [{
                "id": str(item.id),
                "menu_id": str(item.menu_id),
                "name": item.name,
                "description": item.description,
                "price": float(item.price),
                "category": item.category,
                "image_url": item.image_url,
                "is_vegetarian": item.is_vegetarian,
                "is_vegan": item.is_vegan,
                "spice_level": item.spice_level,
                "preparation_time": item.preparation_time,
                "available": item.available,
                "sizes": item.get_sizes(),
                "deals": item.get_deals(),
                "servings": item.get_servings(),
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat()
            } for item in items]
        finally:
            db.close()

    @staticmethod
    def create_menu_item(token: str, main_db: Session, menu_id: str, item_data: MenuItemCreate):
        """Create a new menu item"""
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
        db = tenant_db.get_session()
        try:
            # Verify menu exists
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                raise HTTPException(status_code=404, detail="Menu not found")
            
            item = MenuItem(
                menu_id=menu_id,
                name=item_data.name,
                description=item_data.description,
                price=item_data.price,
                category=item_data.category,
                image_url=item_data.image_url,
                is_vegetarian=item_data.is_vegetarian,
                is_vegan=item_data.is_vegan,
                spice_level=item_data.spice_level,
                preparation_time=item_data.preparation_time,
                available=item_data.available,
                sizes=json.dumps([size.dict() for size in item_data.sizes]) if item_data.sizes else None,
                deals=json.dumps([deal.dict() for deal in item_data.deals]) if item_data.deals else None,
                servings=json.dumps([serving.dict() for serving in item_data.servings]) if item_data.servings else None
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            
            return {
                "id": str(item.id),
                "menu_id": str(item.menu_id),
                "name": item.name,
                "description": item.description,
                "price": float(item.price),
                "category": item.category,
                "image_url": item.image_url,
                "is_vegetarian": item.is_vegetarian,
                "is_vegan": item.is_vegan,
                "spice_level": item.spice_level,
                "preparation_time": item.preparation_time,
                "available": item.available,
                "sizes": item.get_sizes(),
                "deals": item.get_deals(),
                "servings": item.get_servings(),
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat()
            }
        finally:
            db.close()

    @staticmethod
    def update_menu_item(token: str, main_db: Session, item_id: str, item_data: MenuItemUpdate):
        """Update a menu item"""
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
        db = tenant_db.get_session()
        try:
            item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Menu item not found")
            
            # Update fields
            for field, value in item_data.dict(exclude_unset=True).items():
                if field in ['sizes', 'deals', 'servings'] and value is not None:
                    if field == 'sizes':
                        setattr(item, field, json.dumps([size.dict() for size in value]))
                    elif field == 'deals':
                        setattr(item, field, json.dumps([deal.dict() for deal in value]))
                    elif field == 'servings':
                        setattr(item, field, json.dumps([serving.dict() for serving in value]))
                else:
                    setattr(item, field, value)
            
            item.updated_at = datetime.utcnow()
            db.commit()
            
            return {"message": "Menu item updated successfully"}
        finally:
            db.close()

    @staticmethod
    def delete_menu_item(token: str, main_db: Session, item_id: str):
        """Delete a menu item"""
        tenant_db = AdminController.get_tenant_db_by_token(token, main_db)
        
        db = tenant_db.get_session()
        try:
            item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
            if not item:
                raise HTTPException(status_code=404, detail="Menu item not found")
            
            db.delete(item)
            db.commit()
            
            return {"message": "Menu item deleted successfully"}
        finally:
            db.close()