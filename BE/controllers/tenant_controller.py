from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from typing import Optional
import uuid
from datetime import datetime

from database.tenant_db import TenantDatabase
from models.tenant_models import Session as ChatSession, Message, MenuItem, MessageSender
from models.main_models import Restaurant
from schemas.tenant_schemas import ChatMessage, ChatResponse, SessionResponse
from services.ai_service import AIService
from services.image_service import upload_image
from utils.rate_limit import check_rate_limit
import json

class TenantController:
    @staticmethod
    def get_tenant_db_by_slug(slug: str, main_db: Session):
        """Get tenant database by restaurant slug"""
        restaurant = main_db.query(Restaurant).filter(Restaurant.slug == slug).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        from database.tenant_db import get_tenant_db_from_url
        return get_tenant_db_from_url(restaurant.db_url), restaurant

    @staticmethod
    def list_restaurants(main_db: Session):
        """Get list of all restaurants"""
        restaurants = main_db.query(Restaurant).all()
        return [{
            "slug": restaurant.slug,
            "name": restaurant.name,
            "id": str(restaurant.id),
            "description": restaurant.description or f"Delicious food from {restaurant.name}",
            "location": restaurant.location or "City Center",
            "image": restaurant.image_url or "https://images.pexels.com/photos/958545/pexels-photo-958545.jpeg?auto=compress&cs=tinysrgb&w=800"
        } for restaurant in restaurants]

    @staticmethod
    def create_session(slug: str, main_db: Session) -> SessionResponse:
        """Create a new chat session for a restaurant"""
        restaurant = main_db.query(Restaurant).filter(Restaurant.slug == slug).first()
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        # Get tenant database
        tenant_db, _ = TenantController.get_tenant_db_by_slug(slug, main_db)
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

    @staticmethod
    async def chat_with_bot(slug: str, message: ChatMessage, main_db: Session) -> ChatResponse:
        """Handle chat with restaurant AI bot"""
        
        tenant_db, restaurant = TenantController.get_tenant_db_by_slug(slug, main_db)
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
            from models.tenant_models import TokenUsage
            token_usage = TokenUsage(
                session_id=session.id,
                tokens=token_count,
                model="gemini-2.0-flash"
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

    @staticmethod
    def get_menu(slug: str, main_db: Session, search: Optional[str] = None):
        """Get restaurant menu items"""
        
        tenant_db, _ = TenantController.get_tenant_db_by_slug(slug, main_db)
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

    @staticmethod
    async def upload_payment_proof(slug: str, file: UploadFile, main_db: Session):
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

    @staticmethod
    def get_session_messages(slug: str, session_id: str, main_db: Session, limit: int = 50):
        """Get messages for a session"""
        
        tenant_db, _ = TenantController.get_tenant_db_by_slug(slug, main_db)
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