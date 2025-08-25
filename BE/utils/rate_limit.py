from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from database.tenant_db import TokenUsage

RATE_LIMIT_TOKENS = 10000  # 10,000 tokens per 24 hours
RATE_LIMIT_HOURS = 24

def check_rate_limit(db: Session, session_id: str) -> bool:
    """Check if session is within rate limit"""
    
    # Calculate 24h window
    now = datetime.utcnow()
    window_start = now - timedelta(hours=RATE_LIMIT_HOURS)
    
    # Get token usage in last 24h
    total_tokens = db.query(func.coalesce(func.sum(TokenUsage.tokens), 0)).filter(
        and_(
            TokenUsage.session_id == session_id,
            TokenUsage.created_at >= window_start
        )
    ).scalar()
    
    return (total_tokens or 0) < RATE_LIMIT_TOKENS