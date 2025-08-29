from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, UUID, DECIMAL, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.schema import ForeignKey
import uuid
from datetime import datetime
import enum
import json

TenantBase = declarative_base()

# Enums
class OrderStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    in_process = "in_process"
    ready = "ready"
    in_delivery = "in_delivery"
    delivered = "delivered"
    cancelled = "cancelled"

class PaymentStatus(enum.Enum):
    unpaid = "unpaid"
    paid = "paid"

class MessageSender(enum.Enum):
    user = "user"
    bot = "bot"

# Tenant Models
class Settings(TenantBase):
    __tablename__ = "settings"
    
    id = Column(Boolean, primary_key=True, default=True)
    cancellation_window_minutes = Column(Integer, nullable=False, default=15)
    payment_details = Column(Text, nullable=False)
    timezone = Column(String(64), nullable=False, default='Asia/Karachi')

class Session(TenantBase):
    __tablename__ = "sessions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_name = Column(String(160))
    customer_phone = Column(String(50))
    customer_email = Column(String(255))
    delivery_address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(TenantBase):
    __tablename__ = "messages"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    sender = Column(Enum(MessageSender), nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class TokenUsage(TenantBase):
    __tablename__ = "token_usage"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    tokens = Column(Integer, nullable=False)
    model = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Menu(TenantBase):
    __tablename__ = "menus"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(160))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MenuItem(TenantBase):
    __tablename__ = "menu_items"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menu_id = Column(PG_UUID(as_uuid=True), ForeignKey('menus.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(160), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    sizes = Column(Text)  # JSON string for different sizes and prices
    deals = Column(Text)  # JSON string for deals/offers
    servings = Column(Text)  # JSON string for different serving options
    category = Column(String(100))
    image_url = Column(Text)
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    spice_level = Column(Integer, default=0)  # 0-5 scale
    preparation_time = Column(Integer, default=15)  # minutes
    available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_sizes(self):
        """Parse sizes JSON"""
        if self.sizes:
            try:
                return json.loads(self.sizes)
            except:
                return []
        return []
    
    def get_deals(self):
        """Parse deals JSON"""
        if self.deals:
            try:
                return json.loads(self.deals)
            except:
                return []
        return []
    
    def get_servings(self):
        """Parse servings JSON"""
        if self.servings:
            try:
                return json.loads(self.servings)
            except:
                return []
        return []

class Order(TenantBase):
    __tablename__ = "orders"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='RESTRICT'), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.unpaid)
    total_price = Column(DECIMAL(10, 2), nullable=False, default=0)
    payment_proof_text = Column(Text)
    payment_proof_image_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(TenantBase):
    __tablename__ = "order_items"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(PG_UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    menu_item_id = Column(PG_UUID(as_uuid=True), ForeignKey('menu_items.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)