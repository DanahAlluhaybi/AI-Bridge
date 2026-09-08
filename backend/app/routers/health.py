"""
routers/health.py
------------------
A "router" groups related endpoints together. Right now we only have
one group (health/status), but this pattern is why Phase 2 onward will
add files like routers/systems.py, routers/readiness.py, routers/
governance.py, etc. instead of dumping everything into one giant file.
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
    Called by the frontend Dashboard on load.

    What it proves, step by step:
    1. The FastAPI server received the HTTP request (routing works).
    2. `Depends(get_db)` successfully opened a SQLite session (the
       database file is readable/writable).
    3. We write one row (INSERT) and read a count (SELECT) -- so both
       directions of talking to the database are exercised, not just one.
    4. We return JSON, which the browser's fetch() call on the frontend
       will parse and render.
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
