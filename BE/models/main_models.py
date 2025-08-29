from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from datetime import datetime

Base = declarative_base()

class SuperAdmin(Base):
    __tablename__ = "super_admins"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(120), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(80), unique=True, nullable=False, index=True)
    name = Column(String(160), nullable=False)
    description = Column(Text)
    location = Column(String(255))
    image_url = Column(Text)
    admin_username = Column(String(120), unique=True, nullable=False)
    admin_password_hash = Column(Text, nullable=False)
    admin_email = Column(String(255), nullable=False)
    db_url = Column(Text, nullable=False)  # Single database URL instead of separate fields
    gemini_api_key = Column(Text)  # Per-restaurant Gemini API key
    cloudinary_config = Column(Text)  # JSON config for Cloudinary
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AdminOTP(Base):
    __tablename__ = "admin_otp"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(PG_UUID(as_uuid=True), nullable=False)
    code_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False)