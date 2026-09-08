"""
routers/systems.py
-------------------
Full CRUD (Create, Read, Update, Delete) for enterprise systems.

Five endpoints, matching the Phase 2 spec exactly:
    GET    /api/systems         -> list all (with optional filters)
    GET    /api/systems/{id}    -> get one
    POST   /api/systems         -> create
    PUT    /api/systems/{id}    -> update
    DELETE /api/systems/{id}    -> delete

Every function follows the same shape: accept validated input (FastAPI
+ Pydantic already checked it before we get here), do one thing to the
database via SQLAlchemy, return something JSON-serializable (FastAPI
converts it using the `response_model` schema).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter()


@router.get("/systems", response_model=List[schemas.EnterpriseSystemOut])
def list_systems(
    status: Optional[schemas.SystemStatus] = Query(
        default=None, description="Filter by exact status"
    ),
    integration_type: Optional[schemas.IntegrationType] = Query(
        default=None, description="Filter by exact integration type"
    ),
    search: Optional[str] = Query(
        default=None, description="Case-insensitive match on system name"
    ),
    db: Session = Depends(get_db),
):
    """
    The frontend actually filters client-side for instant feedback (see
    EnterpriseSystems.tsx), so in normal use this endpoint is called
    with no query parameters and just returns everything. The filters
    below are still real and independently testable from /docs --
    once there are hundreds of systems instead of five, filtering on
    the server (so the browser never downloads rows it won't show) is
    what you'd switch to.
    """
    query = db.query(models.EnterpriseSystem)

    if status is not None:
        query = query.filter(models.EnterpriseSystem.status == status.value)
    if integration_type is not None:
        query = query.filter(
            models.EnterpriseSystem.integration_type == integration_type.value
        )
    if search:
        query = query.filter(models.EnterpriseSystem.name.ilike(f"%{search}%"))

    return query.order_by(models.EnterpriseSystem.id).all()


@router.get("/systems/{system_id}", response_model=schemas.EnterpriseSystemOut)
def get_system(system_id: int, db: Session = Depends(get_db)):
    system = db.get(models.EnterpriseSystem, system_id)
    if system is None:
        raise HTTPException(status_code=404, detail="Enterprise system not found")
    return system


@router.post(
    "/systems", response_model=schemas.EnterpriseSystemOut, status_code=201
)
def create_system(
    payload: schemas.EnterpriseSystemCreate, db: Session = Depends(get_db)
):
    # payload.model_dump() turns the validated Pydantic object into a
    # plain dict. Because SystemType/IntegrationType/etc. are `str`
    # Enums, their values come out as plain strings ("ERP", not
    # SystemType.ERP) -- exactly what the String columns in models.py
    # expect.
    system = models.EnterpriseSystem(**payload.model_dump())
    db.add(system)
    db.commit()
    db.refresh(system)
    return system


@router.put("/systems/{system_id}", response_model=schemas.EnterpriseSystemOut)
def update_system(
    system_id: int,
    payload: schemas.EnterpriseSystemUpdate,
    db: Session = Depends(get_db),
):
    system = db.get(models.EnterpriseSystem, system_id)
    if system is None:
        raise HTTPException(status_code=404, detail="Enterprise system not found")

    # exclude_unset=True is the key detail: it only includes fields the
    # client actually sent, so `{"status": "Connected"}` doesn't wipe
    # out every other field back to null.
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(system, field, value)

    db.commit()
    db.refresh(system)
    return system


@router.delete("/systems/{system_id}", status_code=204)
def delete_system(system_id: int, db: Session = Depends(get_db)):
    system = db.get(models.EnterpriseSystem, system_id)
    if system is None:
        raise HTTPException(status_code=404, detail="Enterprise system not found")
    db.delete(system)
    db.commit()
    return None
