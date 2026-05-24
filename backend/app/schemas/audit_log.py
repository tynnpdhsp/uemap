from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    event_code: str
    occurred_at: datetime
    actor_role: str
    actor_id: Optional[str] = None
    object_type: str
    object_id: Optional[str] = None
    result: str
    description: str
    ip_address: str
