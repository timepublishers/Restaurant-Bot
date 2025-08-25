from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import bcrypt
import jwt
from datetime import datetime, timedelta
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from database.main_db import MainDatabase, Restaurant, AdminOTP, get_main_db
from utils.email import send_otp_email
from utils.auth import create_access_token, verify_token

router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str

class OTPVerifyRequest(BaseModel):
    username: str
    otp: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    restaurant: dict

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_main_db)):
    """Step 1: Validate credentials and send OTP"""
    
    # Find restaurant admin
    restaurant = db.query(Restaurant).filter(
        Restaurant.admin_username == request.username
    ).first()
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not bcrypt.checkpw(request.password.encode('utf-8'), restaurant.admin_password_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Generate and send OTP
    otp_code = secrets.randbelow(900000) + 100000  # 6-digit code
    otp_hash = bcrypt.hashpw(str(otp_code).encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Store OTP in database
    otp_record = AdminOTP(
        restaurant_id=restaurant.id,
        code_hash=otp_hash,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()
    
    # Send OTP via email
    try:
        await send_otp_email(restaurant.admin_email, otp_code, restaurant.name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email"
        )
    
    return {"message": "OTP sent to registered email", "username": request.username}

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_main_db)):
    """Step 2: Verify OTP and issue JWT token"""
    
    # Find restaurant
    restaurant = db.query(Restaurant).filter(
        Restaurant.admin_username == request.username
    ).first()
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username"
        )
    
    # Find valid OTP
    otp_record = db.query(AdminOTP).filter(
        AdminOTP.restaurant_id == restaurant.id,
        AdminOTP.used == False,
        AdminOTP.expires_at > datetime.utcnow()
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP"
        )
    
    # Verify OTP
    if not bcrypt.checkpw(request.otp.encode('utf-8'), otp_record.code_hash.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP"
        )
    
    # Mark OTP as used
    otp_record.used = True
    db.commit()
    
    # Create JWT token
    token_data = {
        "sub": str(restaurant.id),
        "username": restaurant.admin_username,
        "slug": restaurant.slug,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        restaurant={
            "id": str(restaurant.id),
            "slug": restaurant.slug,
            "name": restaurant.name,
            "admin_email": restaurant.admin_email
        }
    )

@router.get("/me")
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated admin info"""
    try:
        payload = verify_token(credentials.credentials)
        return {
            "id": payload.get("sub"),
            "username": payload.get("username"),
            "slug": payload.get("slug")
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )