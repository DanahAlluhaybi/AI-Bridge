"""
Endpoints for Human Approval (Phase 9):

    GET  /api/approvals                   -> list approval requests (optionally filtered by status)
    POST /api/approvals/{id}/decide        -> a human approves or rejects one

An ApprovalRequest only ever exists because a use case's policy
decision came back HUMAN_APPROVAL (see routers/use_cases.py) -- there's
no way to create one directly. Deciding one updates both the request
itself and the linked AIUseCase.status together, so the two never
disagree about where a use case stands.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import audit, models, schemas
from ..database import get_db

router = APIRouter()


def _get_approval_or_404(approval_id: int, db: Session) -> models.ApprovalRequest:
    approval = db.get(models.ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return approval


def _approval_out(
    approval: models.ApprovalRequest, use_case_name: str, system_name: str
) -> schemas.ApprovalRequestOut:
    return schemas.ApprovalRequestOut(
        id=approval.id,
        use_case_id=approval.use_case_id,
        use_case_name=use_case_name,
        system_name=system_name,
        status=approval.status,
        reason=approval.reason,
        decided_by=approval.decided_by,
        decision_notes=approval.decision_notes,
        created_at=approval.created_at,
        decided_at=approval.decided_at,
    )


def _names_for(use_case: models.AIUseCase, db: Session) -> str:
    system = db.get(models.EnterpriseSystem, use_case.system_id)
    return system.name if system else "Unknown system"


@router.get("/approvals", response_model=List[schemas.ApprovalRequestOut])
def list_approvals(status: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Newest first. `status` defaults to showing every request; pass
    ?status=Pending to get just the ones waiting on a decision -- the
    Approval Center's main view.
    """
    query = db.query(models.ApprovalRequest)
    if status is not None:
        query = query.filter(models.ApprovalRequest.status == status)
    approvals = query.order_by(models.ApprovalRequest.id.desc()).all()

    out = []
    for approval in approvals:
        use_case = db.get(models.AIUseCase, approval.use_case_id)
        use_case_name = use_case.name if use_case else "Unknown use case"
        system_name = _names_for(use_case, db) if use_case else "Unknown system"
        out.append(_approval_out(approval, use_case_name, system_name))
    return out


@router.post("/approvals/{approval_id}/decide", response_model=schemas.ApprovalRequestOut)
def decide_approval(
    approval_id: int, payload: schemas.ApprovalDecision, db: Session = Depends(get_db)
):
    approval = _get_approval_or_404(approval_id, db)
    if approval.status != "Pending":
        raise HTTPException(status_code=400, detail="This approval has already been decided")

    use_case = db.get(models.AIUseCase, approval.use_case_id)
    if use_case is None:
        raise HTTPException(status_code=404, detail="The use case behind this approval no longer exists")

    approval.status = "Approved" if payload.approve else "Rejected"
    approval.decided_by = payload.decided_by
    approval.decision_notes = payload.notes
    approval.decided_at = datetime.now(timezone.utc)
    use_case.status = approval.status
    db.commit()
    db.refresh(approval)

    audit.log(
        db,
        action="approval.decided",
        summary=f'"{use_case.name}" {approval.status.lower()} by {payload.decided_by}',
        entity_type="use_case",
        entity_id=use_case.id,
    )

    return _approval_out(approval, use_case.name, _names_for(use_case, db))
