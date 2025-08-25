from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta

from database.tenant_db import TenantDatabase, Session as ChatSession, Message, MenuItem, Order, OrderItem, Settings, TokenUsage, MessageSender
from database.main_db import Restaurant, get_main_db
from services.ai_service import AIService
from services.image_service import upload_image
from utils.rate_limit import check_rate_limit
import json

router = APIRouter()
security = HTTPBearer()

def get_tenant_db_by_slug(slug: str, main_db: Session = Depends(get_main_db)):
    """Get tenant database by restaurant slug"""
    restaurant = main_db.query(Restaurant).filter(Restaurant.slug == slug).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Build tenant DB connection
    from database.tenant_db import get_tenant_db
    db_config = {
        'db_host': restaurant.db_host,
        'db_port': restaurant.db_port,
        'db_name': restaurant.db_name,
        'db_user': restaurant.db_user,
        'db_password': restaurant.db_password
    }
    
    return get_tenant_db(db_config), restaurant

class ChatMessage(BaseModel):
    content: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    function_calls: Optional[List[Dict[str, Any]]] = None

class SessionResponse(BaseModel):
    session_id: str
    restaurant: Dict[str, Any]

@router.get("/restaurants")
async def list_restaurants(main_db: Session = Depends(get_main_db)):
    """Get list of all restaurants"""
    restaurants = main_db.query(Restaurant).all()
    return [{
        "slug": restaurant.slug,
        "name": restaurant.name,
        "id": str(restaurant.id),
        "description": f"Delicious food from {restaurant.name}",
        "location": "City Center",
        "image": "https://images.pexels.com/photos/958545/pexels-photo-958545.jpeg?auto=compress&cs=tinysrgb&w=800"
    } for restaurant in restaurants]

@router.post("/{slug}/session", response_model=SessionResponse)
async def create_session(
    slug: str,
    main_db: Session = Depends(get_main_db)
):
    """Create a new chat session for a restaurant"""
    restaurant = main_db.query(Restaurant).filter(Restaurant.slug == slug).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Get tenant database
    tenant_db, _ = get_tenant_db_by_slug(slug, main_db)
    db = tenant_db.get_session()
    
    try:
        # Create new session
        session = ChatSession(id=uuid.uuid4())
        db.add(session)
        db.commit()
        
        return SessionResponse(
            session_id=str(session.id),
            restaurant={
                "id": str(restaurant.id),
                "slug": restaurant.slug,
                "name": restaurant.name,
                "description": f"Welcome to {restaurant.name}! I'm your AI assistant ready to help you order delicious food."
            }
        )
    finally:
        db.close()

@router.post("/{slug}/chat", response_model=ChatResponse)
async def chat_with_bot(
    slug: str,
    message: ChatMessage,
    main_db: Session = Depends(get_main_db)
):
    """Handle chat with restaurant AI bot"""
    
    tenant_db, restaurant = get_tenant_db_by_slug(slug, main_db)
    db = tenant_db.get_session()
    try:
        # Get or create session
        if message.session_id:
            session = db.query(ChatSession).filter(ChatSession.id == message.session_id).first()
            if not session:
                session = ChatSession(id=message.session_id)
                db.add(session)
        else:
            session = ChatSession(id=uuid.uuid4())
            db.add(session)
        
        # Check rate limit
        session_id_str = str(session.id)
        if not check_rate_limit(db, session_id_str):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Store user message
        user_message = Message(
            session_id=session.id,
            sender=MessageSender.user,
            content=message.content
        )
        db.add(user_message)
        db.commit()
        
        # Get AI service
        restaurant_info = {
            "id": str(restaurant.id),
            "slug": restaurant.slug,
            "name": restaurant.name,
            "gemini_api_key": restaurant.gemini_api_key,
            "cloudinary_config": json.loads(restaurant.cloudinary_config) if restaurant.cloudinary_config else {}
        }
        ai_service = AIService(restaurant_info, tenant_db)
        
        # Process message with AI
        bot_response, function_calls, token_count = await ai_service.process_message(
            session_id_str, message.content
        )
        
        # Store bot response
        bot_message = Message(
            session_id=session.id,
            sender=MessageSender.bot,
            content=bot_response,
            token_count=token_count
        )
        db.add(bot_message)
        
        # Store token usage
        token_usage = TokenUsage(
            session_id=session.id,
            tokens=token_count,
            model="gemini-2.0-flash-exp"
        )
        db.add(token_usage)
        
        db.commit()
        
        return ChatResponse(
            response=bot_response,
            session_id=session_id_str,
            function_calls=function_calls
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )
    finally:
        db.close()

@router.get("/{slug}/menu")
async def get_menu(
    slug: str,
    search: Optional[str] = None,
    main_db: Session = Depends(get_main_db)
):
    """Get restaurant menu items"""
    
    tenant_db, _ = get_tenant_db_by_slug(slug, main_db)
    db = tenant_db.get_session()
    try:
        query = db.query(MenuItem).filter(MenuItem.available == True)
        
        if search:
            query = query.filter(MenuItem.name.ilike(f"%{search}%"))
        
        menu_items = query.all()
        
        return [{
            "id": str(item.id),
            "name": item.name,
            "description": item.description,
            "price": float(item.price),
            "available": item.available
        } for item in menu_items]
        
    finally:
        db.close()

@router.post("/{slug}/upload-payment-proof")
async def upload_payment_proof(
    slug: str,
    file: UploadFile = File(...),
    main_db: Session = Depends(get_main_db)
):
    """Upload payment proof image"""
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    try:
        # Upload to Cloudinary
        image_url = await upload_image(file)
        return {"image_url": image_url}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        )

@router.get("/{slug}/session/{session_id}/messages")
async def get_session_messages(
    slug: str,
    session_id: str,
    limit: int = 50,
    main_db: Session = Depends(get_main_db)
):
    """Get messages for a session"""
    
    tenant_db, _ = get_tenant_db_by_slug(slug, main_db)
    db = tenant_db.get_session()
    try:
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        return [{
            "id": str(msg.id),
            "sender": msg.sender.value,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
            "token_count": msg.token_count
        } for msg in reversed(messages)]
        
    finally:
        db.close()