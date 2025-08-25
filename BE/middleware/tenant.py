from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import json

from database.main_db import MainDatabase, Restaurant
from database.tenant_db import get_tenant_db, TenantDatabase
from utils.auth import verify_token

security = HTTPBearer(auto_error=False)

class TenantMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Extract slug from path
            path_parts = request.url.path.strip("/").split("/")
            if len(path_parts) >= 3 and path_parts[1] == "tenant":
                slug = path_parts[2]
                
                # Get restaurant info from main DB
                with MainDatabase() as main_db:
                    restaurant = main_db.query(Restaurant).filter(
                        Restaurant.slug == slug
                    ).first()
                    
                    if restaurant:
                        # Store restaurant info in request state
                        scope["state"] = getattr(scope.get("state", {}), "restaurant_info", {})
                        scope["state"]["restaurant_info"] = {
                            "id": str(restaurant.id),
                            "slug": restaurant.slug,
                            "name": restaurant.name,
                            "gemini_api_key": restaurant.gemini_api_key,
                            "cloudinary_config": json.loads(restaurant.cloudinary_config) if restaurant.cloudinary_config else {},
                            "db_config": {
                                "db_host": restaurant.db_host,
                                "db_port": restaurant.db_port,
                                "db_name": restaurant.db_name,
                                "db_user": restaurant.db_user,
                                "db_password": restaurant.db_password
                            }
                        }

        await self.app(scope, receive, send)

def get_current_tenant_db(request: Request) -> TenantDatabase:
    """Get tenant database for current request"""
    restaurant_info = getattr(request.state, 'restaurant_info', None)
    
    if not restaurant_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant context found"
        )
    
    return get_tenant_db(restaurant_info['db_config'])