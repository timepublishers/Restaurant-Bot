from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from decimal import Decimal

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None

class SessionUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    delivery_address: Optional[str] = None
    notes: Optional[str] = None

class MenuItemSize(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

class MenuItemDeal(BaseModel):
    name: str
    description: str
    discount_percentage: Optional[float] = None
    discount_amount: Optional[float] = None
    min_quantity: Optional[int] = None

class MenuItemServing(BaseModel):
    name: str
    price_multiplier: float
    description: Optional[str] = None

class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_vegetarian: bool = False
    is_vegan: bool = False
    spice_level: int = 0
    preparation_time: int = 15
    available: bool = True
    sizes: Optional[List[MenuItemSize]] = []
    deals: Optional[List[MenuItemDeal]] = []
    servings: Optional[List[MenuItemServing]] = []

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_vegetarian: Optional[bool] = None
    is_vegan: Optional[bool] = None
    spice_level: Optional[int] = None
    preparation_time: Optional[int] = None
    available: Optional[bool] = None
    sizes: Optional[List[MenuItemSize]] = None
    deals: Optional[List[MenuItemDeal]] = None
    servings: Optional[List[MenuItemServing]] = None

class MenuCreate(BaseModel):
    name: str
    description: Optional[str] = None

class MenuUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None