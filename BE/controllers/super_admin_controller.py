from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status
import bcrypt
from datetime import datetime
from typing import Optional

from models.main_models import Restaurant
from schemas.restaurant_schemas import RestaurantCreate, RestaurantUpdate, RestaurantResponse

class SuperAdminController:
    @staticmethod
    def create_restaurant(restaurant_data: RestaurantCreate, db: Session) -> RestaurantResponse:
        """Create a new restaurant"""
        
        # Check if slug already exists
        existing_restaurant = db.query(Restaurant).filter(
            Restaurant.slug == restaurant_data.slug
        ).first()
        
        if existing_restaurant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Restaurant with this slug already exists"
            )
        
        # Check if admin username already exists
        existing_username = db.query(Restaurant).filter(
            Restaurant.admin_username == restaurant_data.admin_username
        ).first()
        
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin username already exists"
            )
        
        # Hash password
        password_hash = bcrypt.hashpw(
            restaurant_data.admin_password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Create restaurant
        restaurant = Restaurant(
            slug=restaurant_data.slug,
            name=restaurant_data.name,
            description=restaurant_data.description,
            location=restaurant_data.location,
            image_url=restaurant_data.image_url,
            admin_username=restaurant_data.admin_username,
            admin_password_hash=password_hash,
            admin_email=restaurant_data.admin_email,
            db_url=restaurant_data.db_url,
            gemini_api_key=restaurant_data.gemini_api_key,
            cloudinary_config=restaurant_data.cloudinary_config
        )
        
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        
        return RestaurantResponse(
            id=str(restaurant.id),
            slug=restaurant.slug,
            name=restaurant.name,
            description=restaurant.description,
            location=restaurant.location,
            image_url=restaurant.image_url,
            admin_username=restaurant.admin_username,
            admin_email=restaurant.admin_email,
            created_at=restaurant.created_at,
            updated_at=restaurant.updated_at
        )

    @staticmethod
    def get_restaurants(
        db: Session,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None
    ):
        """Get list of restaurants with pagination"""
        
        query = db.query(Restaurant)
        
        # Apply search filter
        if search:
            query = query.filter(
                func.concat(Restaurant.name, ' ', Restaurant.slug, ' ', Restaurant.location)
                .ilike(f"%{search}%")
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        restaurants = query.order_by(desc(Restaurant.created_at)).offset(
            (page - 1) * limit
        ).limit(limit).all()
        
        restaurant_responses = [
            RestaurantResponse(
                id=str(r.id),
                slug=r.slug,
                name=r.name,
                description=r.description,
                location=r.location,
                image_url=r.image_url,
                admin_username=r.admin_username,
                admin_email=r.admin_email,
                created_at=r.created_at,
                updated_at=r.updated_at
            ) for r in restaurants
        ]
        
        return {
            "restaurants": restaurant_responses,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }

    @staticmethod
    def get_restaurant(restaurant_id: str, db: Session) -> RestaurantResponse:
        """Get restaurant by ID"""
        
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found"
            )
        
        return RestaurantResponse(
            id=str(restaurant.id),
            slug=restaurant.slug,
            name=restaurant.name,
            description=restaurant.description,
            location=restaurant.location,
            image_url=restaurant.image_url,
            admin_username=restaurant.admin_username,
            admin_email=restaurant.admin_email,
            created_at=restaurant.created_at,
            updated_at=restaurant.updated_at
        )

    @staticmethod
    def update_restaurant(
        restaurant_id: str, 
        update_data: RestaurantUpdate, 
        db: Session
    ) -> RestaurantResponse:
        """Update restaurant details"""
        
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found"
            )
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(restaurant, field, value)
        
        restaurant.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(restaurant)
        
        return RestaurantResponse(
            id=str(restaurant.id),
            slug=restaurant.slug,
            name=restaurant.name,
            description=restaurant.description,
            location=restaurant.location,
            image_url=restaurant.image_url,
            admin_username=restaurant.admin_username,
            admin_email=restaurant.admin_email,
            created_at=restaurant.created_at,
            updated_at=restaurant.updated_at
        )

    @staticmethod
    def delete_restaurant(restaurant_id: str, db: Session):
        """Delete restaurant"""
        
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found"
            )
        
        db.delete(restaurant)
        db.commit()
        
        return {"message": "Restaurant deleted successfully"}