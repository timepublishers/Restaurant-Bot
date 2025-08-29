from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

from models.main_models import Base, SuperAdmin

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
    
    # Create super admin if not exists
    SUPER_ADMIN_USERNAME = os.getenv("SUPER_ADMIN_USERNAME", "msuhk")
    SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "Hello1234")
    
    db = MainSessionLocal()
    try:
        existing_admin = db.query(SuperAdmin).filter(
            SuperAdmin.username == SUPER_ADMIN_USERNAME
        ).first()
        
        if not existing_admin:
            password_hash = bcrypt.hashpw(SUPER_ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            super_admin = SuperAdmin(username=SUPER_ADMIN_USERNAME, password_hash=password_hash)
            db.add(super_admin)
            db.commit()
            print(f"Super admin created with username: {SUPER_ADMIN_USERNAME}")
    finally:
        db.close()
    
    print("Main database initialized successfully")

def get_main_db():
    db = MainSessionLocal()
    try:
        yield db
    finally:
        db.close()