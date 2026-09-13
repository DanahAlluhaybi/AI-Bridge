"""
audit.py

One tiny helper other routers call right after anything worth keeping
a trail of -- a system created or removed, an assessment run, a use
case proposed, an approval decided, a playground request made. Kept
as a single plain function rather than a class so recording an action
never costs more than one extra line wherever a db session is already
open.
"""

from typing import Optional

from sqlalchemy.orm import Session

from . import models


def log(
    db: Session,
    action: str,
    summary: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
) -> None:
    db.add(models.AuditLogEntry(
        action=action,
        summary=summary,
        entity_type=entity_type,
        entity_id=entity_id,
    ))
    db.commit()
