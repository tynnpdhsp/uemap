from datetime import datetime
from typing import Optional
from bson import ObjectId
from app.core.database import get_db
from app.models.audit_log import AuditLogModel


async def log_event(
    event_code: str,
    actor_role: str,
    actor_id: Optional[ObjectId],
    object_type: str,
    object_id: Optional[str],
    result: str,
    description: str,
    ip_address: str,
) -> None:
    db = get_db()
    audit_log = AuditLogModel(
        event_code=event_code,
        actor_role=actor_role,
        actor_id=actor_id,
        object_type=object_type,
        object_id=object_id,
        result=result,
        description=description,
        ip_address=ip_address,
        occurred_at=datetime.utcnow()
    )
    await db["audit_logs"].insert_one(audit_log.model_dump(by_alias=True, exclude_none=True))
