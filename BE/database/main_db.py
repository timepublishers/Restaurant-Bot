from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Boolean, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(80), unique=True, nullable=False, index=True)
    name = Column(String(160), nullable=False)
    admin_username = Column(String(120), unique=True, nullable=False)
    admin_password_hash = Column(Text, nullable=False)
    admin_email = Column(String(255), nullable=False)
    db_engine = Column(String(20), nullable=False, default="postgres")
    db_host = Column(String(255), nullable=False)
    db_port = Column(Integer, nullable=False)
    db_name = Column(String(255), nullable=False)
    db_user = Column(String(255), nullable=False)
    db_password = Column(Text, nullable=False)
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

# Main database connection
MAIN_DB_URL = os.getenv("MAIN_DB_URL")
if not MAIN_DB_URL:
    raise ValueError("MAIN_DB_URL environment variable is required")

main_engine = create_engine(MAIN_DB_URL, pool_size=10, max_overflow=20)
MainSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=main_engine)

class MainDatabase:
    def __init__(self):
        self.session = MainSessionLocal()
    
    def __enter__(self):
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        self.session.close()

async def init_main_db():
    """Initialize main database tables"""
    Base.metadata.create_all(bind=main_engine)
    print("Main database initialized successfully")

def get_main_db():
    db = MainSessionLocal()
    try:
        yield db
    finally:
        db.close()