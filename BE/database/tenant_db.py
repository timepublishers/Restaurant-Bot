from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict

from models.tenant_models import TenantBase

# Connection cache
tenant_engines: Dict[str, any] = {}

class TenantDatabase:
    def __init__(self, engine):
        self.engine = engine
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def get_session(self):
        return self.SessionLocal()
    
    def init_tables(self):
        """Initialize tenant database tables"""
        TenantBase.metadata.create_all(bind=self.engine)

def get_tenant_db_from_url(db_url: str) -> TenantDatabase:
    """Get or create tenant database connection from URL"""
    cache_key = db_url
    
    if cache_key not in tenant_engines:
        engine = create_engine(
            db_url, 
            pool_size=10, 
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,   # Recycle connections every hour
            connect_args={"connect_timeout": 10}  # Connection timeout
        )
        tenant_db = TenantDatabase(engine)
        tenant_db.init_tables()
        tenant_engines[cache_key] = tenant_db
        print(f"Created new tenant database connection for {cache_key}")
    
    return tenant_engines[cache_key]

def get_tenant_db(restaurant_config) -> TenantDatabase:
    """Legacy function - use get_tenant_db_from_url instead"""
    return get_tenant_db_from_url(restaurant_config['db_url'])