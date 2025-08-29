from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database.main_db import get_main_db
from controllers.auth_controller import AuthController
from schemas.auth_schemas import LoginRequest, OTPVerifyRequest, TokenResponse, SuperAdminLoginRequest
from utils.auth import create_access_token, verify_token

router = APIRouter()
security = HTTPBearer()

@router.post("/login")
async def restaurant_login(request: LoginRequest, db: Session = Depends(get_main_db)):
    """Step 1: Validate credentials and send OTP"""
    return await AuthController.restaurant_login(request, db)

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_restaurant_otp(request: OTPVerifyRequest, db: Session = Depends(get_main_db)):
    """Step 2: Verify OTP and issue JWT token"""
    return await AuthController.verify_restaurant_otp(request, db)

@router.post("/super-admin/login", response_model=TokenResponse)
async def super_admin_login(request: SuperAdminLoginRequest, db: Session = Depends(get_main_db)):
    """Super admin login"""
    return await AuthController.super_admin_login(request, db)

@router.get("/me")
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated admin info"""
    try:
        payload = verify_token(credentials.credentials)
        return {
            "id": payload.get("sub"),
            "username": payload.get("username"),
            "slug": payload.get("slug"),
            "user_type": payload.get("user_type")
        }
    except Exception:
        return {"error": "Invalid or expired token"}