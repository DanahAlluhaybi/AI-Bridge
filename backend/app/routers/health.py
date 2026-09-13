"""
routers/health.py

Health/status endpoint used by the frontend dashboard to confirm the
API is reachable and the database is writable.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import HealthPing

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Writes one HealthPing row and returns a running count, so both a
    write and a read against the database are exercised on every call.
    """
    ping = HealthPing(source="dashboard")
    db.add(ping)
    db.commit()
    db.refresh(ping)

    total_pings = db.query(HealthPing).count()

    return {
        "status": "ok",
        "database": "connected",
        "server_time": datetime.now(timezone.utc).isoformat(),
        "total_health_checks_recorded": total_pings,
    }
