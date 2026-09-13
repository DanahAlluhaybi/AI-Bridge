"""
Endpoint for the Audit Log (Phase 11):

    GET /api/audit-log   -> recent entries, newest first

Read-only by design -- entries are written in one place only, by
audit.log(), from inside the routers that already make changes worth
recording. Named audit_log.py (not audit.py, which is the helper
module this router doesn't need to import) purely to keep the two
apart.
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.get("/audit-log", response_model=List[schemas.AuditLogEntryOut])
def list_audit_log(limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)):
    entries = (
        db.query(models.AuditLogEntry)
        .order_by(models.AuditLogEntry.id.desc())
        .limit(limit)
        .all()
    )
    return entries
