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

from sqlalchemy import JSON, Column, DateTime, Integer, String

from .database import Base


class HealthPing(Base):
    __tablename__ = "health_pings"

    id = Column(Integer, primary_key=True, index=True)
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    source = Column(String, default="unknown")


class EnterpriseSystem(Base):
    """
    Phase 2: one row = one enterprise system that AI Bridge knows about
    (a simulated ERP, HR system, Finance database, etc.). This table is
    the foundation everything from Phase 3 onward hooks into -- the
    adapter pipeline extracts data "from" these, the readiness score is
    calculated "for" one of these, and so on.

    Every column here is a plain string except `data_types`, which is a
    JSON column -- SQLAlchemy stores it as text in SQLite but gives it
    back to us as a real Python list. That's the one field that's
    naturally a list (a system usually carries more than one kind of
    data), so it gets special treatment instead of being crammed into a
    comma-separated string.

    We store classification/status/etc. as plain strings (not a SQL
    ENUM type) and let the API layer (schemas.py) enforce which values
    are allowed. This keeps the database simple and puts validation
    where it's easiest to change later.
    """

    __tablename__ = "enterprise_systems"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    system_type = Column(String, nullable=False)
    department = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    integration_type = Column(String, nullable=False)
    data_types = Column(JSON, nullable=False, default=list)
    data_classification = Column(String, nullable=False)
    security_level = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Pending")
    # Not in the original spec's field list, but every "Integration" in
    # a real system has some kind of address -- a URL, a file path, a
    # connection string. We simulate one so System Details has something
    # honest to show instead of a placeholder.
    data_source = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
