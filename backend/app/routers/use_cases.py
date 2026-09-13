"""
Endpoints for AI Use Cases (Phase 7) and the AI Passport (Phase 8):

    GET    /api/use-cases                 -> list every use case
    GET    /api/use-cases/{id}            -> one use case
    POST   /api/use-cases                 -> propose a new one
    DELETE /api/use-cases/{id}            -> remove one
    GET    /api/use-cases/{id}/passport   -> the AI Passport summary

Creating a use case runs it through the governance policy (see
use_cases/policy.py) immediately, using the system's current
Readiness + Risk + AI Adoption decision, and stores the result on the
use case itself rather than recomputing it later -- a use case's
recorded decision is a snapshot of what was decided when it was
proposed. A HUMAN_APPROVAL outcome also creates a Pending
ApprovalRequest (see routers/approvals.py) in the same step.

No PUT here yet -- changing the requested automation level would mean
re-running the policy and potentially invalidating an existing
approval decision, which is left for a later pass.
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import audit, models, schemas
from ..adoption import decision as adoption_decision
from ..adoption.engine import _latest_readiness_score, _latest_risk_level
from ..database import get_db
from ..use_cases import policy

router = APIRouter()


def _get_system_or_404(system_id: int, db: Session) -> models.EnterpriseSystem:
    system = db.get(models.EnterpriseSystem, system_id)
    if system is None:
        raise HTTPException(status_code=404, detail="Enterprise system not found")
    return system


def _get_use_case_or_404(use_case_id: int, db: Session) -> models.AIUseCase:
    use_case = db.get(models.AIUseCase, use_case_id)
    if use_case is None:
        raise HTTPException(status_code=404, detail="Use case not found")
    return use_case


def _use_case_out(use_case: models.AIUseCase, system_name: str) -> schemas.AIUseCaseOut:
    return schemas.AIUseCaseOut(
        id=use_case.id,
        system_id=use_case.system_id,
        system_name=system_name,
        name=use_case.name,
        purpose=use_case.purpose,
        owner=use_case.owner,
        requested_automation_level=use_case.requested_automation_level,
        policy_decision=use_case.policy_decision,
        policy_reason=use_case.policy_reason,
        status=use_case.status,
        created_at=use_case.created_at,
    )


@router.get("/use-cases", response_model=List[schemas.AIUseCaseOut])
def list_use_cases(db: Session = Depends(get_db)):
    use_cases = db.query(models.AIUseCase).order_by(models.AIUseCase.id.desc()).all()
    systems_by_id = {s.id: s.name for s in db.query(models.EnterpriseSystem).all()}
    return [_use_case_out(uc, systems_by_id.get(uc.system_id, "Unknown system")) for uc in use_cases]


@router.get("/use-cases/{use_case_id}", response_model=schemas.AIUseCaseOut)
def get_use_case(use_case_id: int, db: Session = Depends(get_db)):
    use_case = _get_use_case_or_404(use_case_id, db)
    system = db.get(models.EnterpriseSystem, use_case.system_id)
    return _use_case_out(use_case, system.name if system else "Unknown system")


@router.post("/use-cases", response_model=schemas.AIUseCaseOut, status_code=201)
def create_use_case(payload: schemas.AIUseCaseCreate, db: Session = Depends(get_db)):
    system = _get_system_or_404(payload.system_id, db)

    readiness_score = _latest_readiness_score(system.id, db)
    risk_level = _latest_risk_level(system.id, db)
    decision, _ = adoption_decision.determine_adoption_decision(readiness_score, risk_level)

    policy_decision, policy_reason = policy.determine_policy(
        payload.requested_automation_level.value, risk_level, decision
    )

    use_case = models.AIUseCase(
        system_id=system.id,
        name=payload.name,
        purpose=payload.purpose,
        owner=payload.owner,
        requested_automation_level=payload.requested_automation_level.value,
        policy_decision=policy_decision,
        policy_reason=policy_reason,
        status=policy.STATUS_FOR_POLICY[policy_decision],
    )
    db.add(use_case)
    db.commit()
    db.refresh(use_case)

    if policy_decision == policy.HUMAN_APPROVAL:
        db.add(models.ApprovalRequest(use_case_id=use_case.id, reason=policy_reason))
        db.commit()

    audit.log(
        db,
        action="use_case.created",
        summary=f'"{use_case.name}" proposed for {system.name} — {policy_decision}',
        entity_type="use_case",
        entity_id=use_case.id,
    )

    return _use_case_out(use_case, system.name)


@router.delete("/use-cases/{use_case_id}", status_code=204)
def delete_use_case(use_case_id: int, db: Session = Depends(get_db)):
    use_case = _get_use_case_or_404(use_case_id, db)
    db.delete(use_case)
    db.commit()
    return None


@router.get("/use-cases/{use_case_id}/passport", response_model=schemas.AIPassportOut)
def get_ai_passport(use_case_id: int, db: Session = Depends(get_db)):
    use_case = _get_use_case_or_404(use_case_id, db)
    system = _get_system_or_404(use_case.system_id, db)

    return schemas.AIPassportOut(
        use_case_id=use_case.id,
        use_case_name=use_case.name,
        purpose=use_case.purpose,
        owner=use_case.owner,
        system_id=system.id,
        system_name=system.name,
        data_classification=system.data_classification,
        security_level=system.security_level,
        readiness_score=_latest_readiness_score(system.id, db),
        risk_level=_latest_risk_level(system.id, db),
        adoption_decision=adoption_decision.determine_adoption_decision(
            _latest_readiness_score(system.id, db), _latest_risk_level(system.id, db)
        )[0],
        requested_automation_level=use_case.requested_automation_level,
        policy_decision=use_case.policy_decision,
        policy_reason=use_case.policy_reason,
        use_case_status=use_case.status,
        use_case_created_at=use_case.created_at,
        generated_at=datetime.now(timezone.utc),
    )
