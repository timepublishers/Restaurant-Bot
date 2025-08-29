from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from database.main_db import get_main_db
from controllers.tenant_controller import TenantController
from schemas.tenant_schemas import ChatMessage, ChatResponse, SessionResponse

router = APIRouter()

@router.get("/restaurants")
async def list_restaurants(main_db: Session = Depends(get_main_db)):
    """Get list of all restaurants"""
    return TenantController.list_restaurants(main_db)

@router.post("/{slug}/session", response_model=SessionResponse)
async def create_session(
    slug: str,
    main_db: Session = Depends(get_main_db)
):
    """Create a new chat session for a restaurant"""
    return TenantController.create_session(slug, main_db)

@router.post("/{slug}/chat", response_model=ChatResponse)
async def chat_with_bot(
    slug: str,
    message: ChatMessage,
    main_db: Session = Depends(get_main_db)
):
    """Handle chat with restaurant AI bot"""
    return await TenantController.chat_with_bot(slug, message, main_db)

@router.get("/{slug}/menu")
async def get_menu(
    slug: str,
    search: Optional[str] = None,
    main_db: Session = Depends(get_main_db)
):
    """Get restaurant menu items"""
    return TenantController.get_menu(slug, main_db, search)

@router.post("/{slug}/upload-payment-proof")
async def upload_payment_proof(
    slug: str,
    file: UploadFile = File(...),
    main_db: Session = Depends(get_main_db)
):
    """Upload payment proof image"""
    return await TenantController.upload_payment_proof(slug, file, main_db)

@router.get("/{slug}/session/{session_id}/messages")
async def get_session_messages(
    slug: str,
    session_id: str,
    limit: int = 50,
    main_db: Session = Depends(get_main_db)
):
    """Get messages for a session"""
    return TenantController.get_session_messages(slug, session_id, main_db, limit)