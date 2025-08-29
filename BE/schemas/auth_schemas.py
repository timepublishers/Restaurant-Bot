from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class SuperAdminLoginRequest(BaseModel):
    username: str
    password: str

class OTPVerifyRequest(BaseModel):
    username: str
    otp: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    restaurant: Optional[dict] = None
    user_type: str = "restaurant_admin"  # or "super_admin"