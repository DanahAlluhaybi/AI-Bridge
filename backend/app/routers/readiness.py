"""
Endpoints for the AI Readiness Assessment:

    POST /api/systems/{system_id}/assess            -> run a new assessment, save + return it
    GET  /api/systems/{system_id}/readiness/latest   -> most recent assessment for one system
    GET  /api/systems/{system_id}/readiness/history  -> every past assessment for one system
    GET  /api/readiness/{assessment_id}              -> one assessment by its own id
    GET  /api/readiness/summary                      -> the numbers the Dashboard shows

Assessing is deliberately its own action (a button the user clicks),
not something that happens automatically -- an assessment is a
snapshot of "as of right now", and a system's profile or adapter
results can change between assessments. Re-running it is how you get
an up-to-date score, the same way re-running the adapter gets you a
fresh processing job.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..readiness.engine import GAP_MESSAGES, WEAK_DIMENSION_THRESHOLD, run_assessment

router = APIRouter()


def _assessment_out(
    assessment: models.AIReadinessAssessment, system_name: str
) -> schemas.AIReadinessAssessmentOut:
    return schemas.AIReadinessAssessmentOut(
        id=assessment.id,
        system_id=assessment.system_id,
        system_name=system_name,
        overall_score=assessment.overall_score,
        readiness_level=assessment.readiness_level,
        dimension_scores=assessment.dimension_scores,
        identified_gaps=[schemas.DimensionGap(**gap) for gap in assessment.identified_gaps],
        recommendations=assessment.recommendations,
        created_at=assessment.created_at,
    )


def _get_system_or_404(system_id: int, db: Session) -> models.EnterpriseSystem:
    system = db.get(models.EnterpriseSystem, system_id)
    if system is None:
        raise HTTPException(status_code=404, detail="Enterprise system not found")
    return system


@router.post("/systems/{system_id}/assess", response_model=schemas.AIReadinessAssessmentOut, status_code=201)
def assess_system(system_id: int, db: Session = Depends(get_db)):
    system = _get_system_or_404(system_id, db)
    assessment = run_assessment(system, db)
    return _assessment_out(assessment, system.name)


@router.get("/systems/{system_id}/readiness/latest", response_model=schemas.AIReadinessAssessmentOut)
def get_latest_assessment(system_id: int, db: Session = Depends(get_db)):
    system = _get_system_or_404(system_id, db)
    assessment = (
        db.query(models.AIReadinessAssessment)
        .filter(models.AIReadinessAssessment.system_id == system_id)
        .order_by(models.AIReadinessAssessment.id.desc())
        .first()
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="This system has not been assessed yet")
    return _assessment_out(assessment, system.name)


@router.get("/systems/{system_id}/readiness/history", response_model=List[schemas.AIReadinessAssessmentOut])
def get_assessment_history(system_id: int, db: Session = Depends(get_db)):
    system = _get_system_or_404(system_id, db)
    assessments = (
        db.query(models.AIReadinessAssessment)
        .filter(models.AIReadinessAssessment.system_id == system_id)
        .order_by(models.AIReadinessAssessment.id.desc())
        .all()
    )
    return [_assessment_out(a, system.name) for a in assessments]


@router.get("/readiness/summary", response_model=schemas.ReadinessSummary)
def get_readiness_summary(db: Session = Depends(get_db)):
    """
    Powers the Dashboard. Uses each system's most recent assessment
    only -- a system assessed three times still counts once, using its
    latest result, so re-assessing never inflates the counts.
    """
    systems = db.query(models.EnterpriseSystem).all()

    latest_by_system = {}
    for system in systems:
        latest = (
            db.query(models.AIReadinessAssessment)
            .filter(models.AIReadinessAssessment.system_id == system.id)
            .order_by(models.AIReadinessAssessment.id.desc())
            .first()
        )
        if latest is not None:
            latest_by_system[system.id] = (system, latest)

    assessed = list(latest_by_system.values())
    level_counts = {"AI Ready": 0, "Mostly Ready": 0, "Needs Improvement": 0, "Not Ready": 0}
    governance_gaps: List[schemas.SystemGovernanceGap] = []

    for system, assessment in assessed:
        level_counts[assessment.readiness_level] = level_counts.get(assessment.readiness_level, 0) + 1

        governance_score = assessment.dimension_scores.get("Governance")
        if governance_score is not None and governance_score < WEAK_DIMENSION_THRESHOLD:
            governance_gaps.append(
                schemas.SystemGovernanceGap(
                    system_id=system.id,
                    system_name=system.name,
                    score=governance_score,
                    description=GAP_MESSAGES["Governance"],
                )
            )

    average_score = (
        round(sum(a.overall_score for _, a in assessed) / len(assessed), 1) if assessed else None
    )
    # Worst governance gaps first -- the systems that need the most attention.
    governance_gaps.sort(key=lambda g: g.score)

    return schemas.ReadinessSummary(
        systems_total=len(systems),
        systems_assessed=len(assessed),
        average_score=average_score,
        ai_ready_count=level_counts["AI Ready"],
        mostly_ready_count=level_counts["Mostly Ready"],
        needs_improvement_count=level_counts["Needs Improvement"],
        not_ready_count=level_counts["Not Ready"],
        top_governance_gaps=governance_gaps[:5],
    )


@router.get("/readiness/{assessment_id}", response_model=schemas.AIReadinessAssessmentOut)
def get_assessment_by_id(assessment_id: int, db: Session = Depends(get_db)):
    assessment = db.get(models.AIReadinessAssessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    system = db.get(models.EnterpriseSystem, assessment.system_id)
    return _assessment_out(assessment, system.name if system else "Unknown system")
