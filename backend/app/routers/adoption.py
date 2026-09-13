"""
Endpoints for AI Adoption & Automation Opportunities:

    GET /api/systems/{system_id}/adoption   -> one system's adoption decision + ranked opportunities
    GET /api/adoption/summary                 -> every system, ranked by adoption suitability

There's no POST/"assess" endpoint here, unlike readiness and risk --
an AI Adoption decision is always a live read of whatever Readiness
and Risk assessments already exist for a system (see
adoption/engine.py), not a separate thing a user runs and saves.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..adoption import engine
from ..database import get_db

router = APIRouter()


def _get_system_or_404(system_id: int, db: Session) -> models.EnterpriseSystem:
    system = db.get(models.EnterpriseSystem, system_id)
    if system is None:
        raise HTTPException(status_code=404, detail="Enterprise system not found")
    return system


@router.get("/systems/{system_id}/adoption", response_model=schemas.SystemAdoptionOut)
def get_system_adoption(system_id: int, db: Session = Depends(get_db)):
    system = _get_system_or_404(system_id, db)
    return engine.get_system_adoption(system, db)


@router.get("/adoption/summary", response_model=schemas.AdoptionOverview)
def get_adoption_overview(db: Session = Depends(get_db)):
    return schemas.AdoptionOverview(systems=engine.get_adoption_overview(db))
