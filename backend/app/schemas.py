"""
schemas.py
----------
This file is new in Phase 2, and it introduces an idea worth pausing on:
**models.py describes the database table. schemas.py describes the API.**

They look similar but answer different questions:
- models.py (SQLAlchemy): "what does a row in enterprise_systems look
  like in SQLite?"
- schemas.py (Pydantic): "what JSON is a client allowed to send us, and
  what JSON do we promise to send back?"

Why not just use one? A few reasons that matter more as the project
grows:
- The database row has an `id` and `created_at` that the CLIENT should
  never be allowed to set when creating a system -- Pydantic lets us
  define a "Create" shape without those fields, and a separate "Out"
  shape that includes them.
- "Update" requests should be allowed to send only the fields they're
  changing (e.g. just `status`), not the whole object. That needs its
  own shape where every field is optional.
- Pydantic validates incoming data before it ever reaches our database
  code -- e.g. it will reject `"security_level": "Extremely High"`
  automatically, because that's not one of the four allowed values,
  and return a clear 422 error explaining why.

The Enums below (SystemType, IntegrationType, ...) are the actual list
of allowed values for each field. Enterprise governance tools use a
controlled vocabulary like this on purpose -- it's what lets later
phases (readiness scoring, risk rules, dashboards) reliably group and
count systems by type, instead of dealing with free-text like "erp",
"ERP system", "Corporate ERP" all meaning the same thing.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SystemType(str, Enum):
    ERP = "ERP"
    HR = "HR Management"
    FINANCE = "Finance"
    CUSTOMER_SUPPORT = "Customer Support"
    SALES = "Sales"
    OTHER = "Other"


class IntegrationType(str, Enum):
    REST_API = "REST API"
    CSV = "CSV"
    JSON = "JSON"
    SQL_DATABASE = "SQL Database"


class DataClassification(str, Enum):
    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    RESTRICTED = "Restricted"


class SecurityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class SystemStatus(str, Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    PENDING = "Pending"


class EnterpriseSystemBase(BaseModel):
    """Fields every enterprise system has, shared by Create and Out."""

    name: str = Field(min_length=2, max_length=120)
    system_type: SystemType
    department: str = Field(min_length=2, max_length=120)
    owner: str = Field(min_length=2, max_length=160)
    integration_type: IntegrationType
    data_types: List[str] = Field(default_factory=list)
    data_classification: DataClassification
    security_level: SecurityLevel
    status: SystemStatus = SystemStatus.PENDING
    data_source: Optional[str] = None


class EnterpriseSystemCreate(EnterpriseSystemBase):
    """What the client sends us on POST /api/systems."""


class EnterpriseSystemUpdate(BaseModel):
    """
    What the client sends us on PUT /api/systems/{id}.

    Every field is Optional here on purpose: this lets a client update
    just `status`, for example, without having to resend the entire
    record. The router only applies the fields that were actually sent
    (see `exclude_unset=True` in routers/systems.py).
    """

    name: Optional[str] = None
    system_type: Optional[SystemType] = None
    department: Optional[str] = None
    owner: Optional[str] = None
    integration_type: Optional[IntegrationType] = None
    data_types: Optional[List[str]] = None
    data_classification: Optional[DataClassification] = None
    security_level: Optional[SecurityLevel] = None
    status: Optional[SystemStatus] = None
    data_source: Optional[str] = None


class EnterpriseSystemOut(EnterpriseSystemBase):
    """What we send back to the client. Adds the fields the database owns."""

    id: int
    created_at: datetime

    # This tells Pydantic it's fine to build this schema directly from a
    # SQLAlchemy model instance (system.name, system.id, ...) instead of
    # only from a plain dict -- without it, `return system` in the
    # router wouldn't know how to turn an EnterpriseSystem row into JSON.
    model_config = ConfigDict(from_attributes=True)
