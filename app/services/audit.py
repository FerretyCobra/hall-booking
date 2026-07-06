"""Tiny helper to append audit entries. Callers commit as part of their own txn."""
from sqlalchemy.orm import Session

from ..models import AuditLog


def log(db: Session, action: str, *, entity=None, entity_id=None,
        actor=None, actor_ip=None, detail=None):
    db.add(AuditLog(
        action=action, entity=entity, entity_id=entity_id,
        actor=actor, actor_ip=actor_ip, detail=detail,
    ))
