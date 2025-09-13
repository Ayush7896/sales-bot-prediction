from typing import List, Optional
from pydantic import BaseModel

# Request / Response Models
class UserQuery(BaseModel):
    user_query: str
    session_id: str = "default_session"

class BotResponse(BaseModel):
    bot_response: str
    sources: List[str] = []
    is_instant_faq: bool = False
    nudge: Optional[str] = None
