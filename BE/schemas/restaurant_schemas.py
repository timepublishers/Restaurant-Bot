from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class RestaurantCreate(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    admin_username: str
    admin_password: str
    admin_email: EmailStr
    db_url: str
    gemini_api_key: Optional[str] = None
    cloudinary_config: Optional[str] = None

class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    db_url: Optional[str] = None
    gemini_api_key: Optional[str] = None
    cloudinary_config: Optional[str] = None

class RestaurantResponse(BaseModel):
    id: str
    slug: str
    name: str
    description: Optional[str]
    location: Optional[str]
    image_url: Optional[str]
    admin_username: str
    admin_email: str
    created_at: datetime
    updated_at: datetime

class RestaurantListResponse(BaseModel):
    restaurants: list[RestaurantResponse]
    total: int
    page: int
    limit: int
    pages: int