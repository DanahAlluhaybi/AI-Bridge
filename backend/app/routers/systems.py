"""
routers/systems.py

Full CRUD for enterprise systems:
    GET    /api/systems         -> list all (with optional filters)
    GET    /api/systems/{id}    -> get one
    POST   /api/systems         -> create
    PUT    /api/systems/{id}    -> update
    DELETE /api/systems/{id}    -> delete
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
    The frontend filters client-side (see EnterpriseSystems.tsx), so in
    practice this is usually called with no query parameters. The
    filters are still real and testable from /docs, and matter once
    the dataset is too large to send to the browser in one response.
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
    # model_dump() turns the validated Pydantic object into a plain
    # dict; the Enum fields serialize to their string values, which is
    # what the String columns in models.py expect.
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

    # exclude_unset=True: only fields the client actually sent get
    # applied, so a partial update like {"status": "Connected"} doesn't
    # null out every other field.
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
