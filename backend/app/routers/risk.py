"""
Endpoints for the AI Risk Engine:

    POST /api/systems/{system_id}/risk-assess         -> run a new assessment, save + return it
    GET  /api/systems/{system_id}/risk/latest          -> most recent risk assessment for one system
    GET  /api/systems/{system_id}/risk/history         -> every past risk assessment for one system
    GET  /api/risk/{assessment_id}                     -> one assessment by its own id
    GET  /api/risk/summary                             -> the numbers the Dashboard shows

Same shape as routers/readiness.py: assessing is its own action (a
button the user clicks), not something recomputed automatically, since
a risk assessment is a snapshot of "as of right now" and a system's
profile or readiness can change between assessments.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..risk.engine import run_risk_assessment

router = APIRouter()


def _assessment_out(
    assessment: models.AIRiskAssessment, system_name: str
) -> schemas.AIRiskAssessmentOut:
    return schemas.AIRiskAssessmentOut(
        id=assessment.id,
        system_id=assessment.system_id,
        system_name=system_name,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        risk_factors=assessment.risk_factors,
        risk_drivers=[schemas.RiskDriver(**driver) for driver in assessment.risk_drivers],
        created_at=assessment.created_at,
    )


def _get_system_or_404(system_id: int, db: Session) -> models.EnterpriseSystem:
    system = db.get(models.EnterpriseSystem, system_id)
    if system is None:
        raise HTTPException(status_code=404, detail="Enterprise system not found")
    return system


@router.post("/systems/{system_id}/risk-assess", response_model=schemas.AIRiskAssessmentOut, status_code=201)
def assess_risk(system_id: int, db: Session = Depends(get_db)):
    system = _get_system_or_404(system_id, db)
    assessment = run_risk_assessment(system, db)
    return _assessment_out(assessment, system.name)


@router.get("/systems/{system_id}/risk/latest", response_model=schemas.AIRiskAssessmentOut)
def get_latest_risk_assessment(system_id: int, db: Session = Depends(get_db)):
    system = _get_system_or_404(system_id, db)
    assessment = (
        db.query(models.AIRiskAssessment)
        .filter(models.AIRiskAssessment.system_id == system_id)
        .order_by(models.AIRiskAssessment.id.desc())
        .first()
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="This system has not been risk-assessed yet")
    return _assessment_out(assessment, system.name)


@router.get("/systems/{system_id}/risk/history", response_model=List[schemas.AIRiskAssessmentOut])
def get_risk_assessment_history(system_id: int, db: Session = Depends(get_db)):
    system = _get_system_or_404(system_id, db)
    assessments = (
        db.query(models.AIRiskAssessment)
        .filter(models.AIRiskAssessment.system_id == system_id)
        .order_by(models.AIRiskAssessment.id.desc())
        .all()
    )
    return [_assessment_out(a, system.name) for a in assessments]


@router.get("/risk/summary", response_model=schemas.RiskSummary)
def get_risk_summary(db: Session = Depends(get_db)):
    """
    Powers the Dashboard. Uses each system's most recent risk
    assessment only -- a system assessed three times still counts
    once, using its latest result, so re-assessing never inflates the
    counts.
    """
    systems = db.query(models.EnterpriseSystem).all()

    latest_by_system = {}
    for system in systems:
        latest = (
            db.query(models.AIRiskAssessment)
            .filter(models.AIRiskAssessment.system_id == system.id)
            .order_by(models.AIRiskAssessment.id.desc())
            .first()
        )
        if latest is not None:
            latest_by_system[system.id] = (system, latest)

    assessed = list(latest_by_system.values())
    level_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}

    for _, assessment in assessed:
        level_counts[assessment.risk_level] = level_counts.get(assessment.risk_level, 0) + 1

    average_risk_score = (
        round(sum(a.risk_score for _, a in assessed) / len(assessed), 1) if assessed else None
    )

    # Highest risk first -- the systems that need the most attention.
    highest_risk = sorted(assessed, key=lambda pair: pair[1].risk_score, reverse=True)
    highest_risk_systems = [
        schemas.SystemRiskFlag(
            system_id=system.id,
            system_name=system.name,
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level,
        )
        for system, assessment in highest_risk[:5]
    ]

    return schemas.RiskSummary(
        systems_total=len(systems),
        systems_assessed=len(assessed),
        average_risk_score=average_risk_score,
        low_count=level_counts["Low"],
        medium_count=level_counts["Medium"],
        high_count=level_counts["High"],
        critical_count=level_counts["Critical"],
        highest_risk_systems=highest_risk_systems,
    )


@router.get("/risk/{assessment_id}", response_model=schemas.AIRiskAssessmentOut)
def get_risk_assessment_by_id(assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.get(models.AIRiskAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    system = db.get(models.EnterpriseSystem, assessment.system_id)
    return _assessment_out(assessment, system.name if system else "Unknown system")
