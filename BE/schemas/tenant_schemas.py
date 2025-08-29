from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    content: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    function_calls: Optional[List[Dict[str, Any]]] = None

class SessionResponse(BaseModel):
    session_id: str
    restaurant: Dict[str, Any]