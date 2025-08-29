from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import bcrypt
import secrets
from datetime import datetime, timedelta

from models.main_models import Restaurant, AdminOTP, SuperAdmin
from schemas.auth_schemas import LoginRequest, OTPVerifyRequest, SuperAdminLoginRequest
from utils.auth import create_access_token
from utils.email import send_otp_email

class AuthController:
    @staticmethod
    async def restaurant_login(request: LoginRequest, db: Session):
        """Step 1: Validate restaurant admin credentials and send OTP"""
        
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

    @staticmethod
    async def verify_restaurant_otp(request: OTPVerifyRequest, db: Session):
        """Step 2: Verify OTP and issue JWT token for restaurant admin"""
        
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
            "user_type": "restaurant_admin",
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_type": "restaurant_admin",
            "restaurant": {
                "id": str(restaurant.id),
                "slug": restaurant.slug,
                "name": restaurant.name,
                "admin_email": restaurant.admin_email
            }
        }

    @staticmethod
    async def super_admin_login(request: SuperAdminLoginRequest, db: Session):
        """Super admin login"""
        
        # Find super admin
        super_admin = db.query(SuperAdmin).filter(
            SuperAdmin.username == request.username
        ).first()
        
        if not super_admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not bcrypt.checkpw(request.password.encode('utf-8'), super_admin.password_hash.encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create JWT token
        token_data = {
            "sub": str(super_admin.id),
            "username": super_admin.username,
            "user_type": "super_admin",
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_type": "super_admin"
        }