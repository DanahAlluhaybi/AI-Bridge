"""
models.py
---------
Each class here becomes one table in ai_bridge.db.

Phase 1 only needs to prove that the full chain works:
    React (frontend) -> FastAPI (backend) -> SQLite (database)
        -> FastAPI -> React

So instead of building a real business table (EnterpriseSystem, UseCase,
etc. come in later phases), we create one small, honest table: a record
of every time someone asked the backend "are you alive, and can you talk
to the database?". It's simple enough to fully understand, and it's not
throwaway -- the pattern you see here (a Column, a type, a default) is
exactly what every future table will look like.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from .database import Base


class HealthPing(Base):
    __tablename__ = "health_pings"

    id = Column(Integer, primary_key=True, index=True)
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    source = Column(String, default="unknown")
