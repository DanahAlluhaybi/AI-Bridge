"""
Endpoints for the AI Playground (Phase 10):

    POST /api/playground/ask       -> send a prompt through an Approved use case
    GET  /api/playground/history   -> past prompts + responses (optionally filtered by use case)

A prompt is only accepted for a use case whose status is Approved --
this is the whole point of the governance chain: nothing gets to
"run" until a human (or the policy itself) has said it's allowed to.
Responses come from playground/mock_provider.py, a free, deterministic
stand-in for a real model.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import audit, models, schemas
from ..database import get_db
from ..playground.mock_provider import generate_response

router = APIRouter()


def _get_use_case_or_404(use_case_id: int, db: Session) -> models.AIUseCase:
    use_case = db.get(models.AIUseCase, use_case_id)
    if use_case is None:
        raise HTTPException(status_code=404, detail="Use case not found")
    return use_case


def _request_out(request: models.PlaygroundRequest, use_case_name: str) -> schemas.PlaygroundRequestOut:
    return schemas.PlaygroundRequestOut(
        id=request.id,
        use_case_id=request.use_case_id,
        use_case_name=use_case_name,
        prompt=request.prompt,
        response=request.response,
        created_at=request.created_at,
    )


@router.post("/playground/ask", response_model=schemas.PlaygroundRequestOut, status_code=201)
def ask_playground(payload: schemas.PlaygroundRequestCreate, db: Session = Depends(get_db)):
    use_case = _get_use_case_or_404(payload.use_case_id, db)
    if use_case.status != "Approved":
        raise HTTPException(
            status_code=400,
            detail=f'"{use_case.name}" is {use_case.status}, not Approved -- it cannot be run in the Playground yet.',
        )

    response_text = generate_response(payload.prompt, use_case.name)

    request = models.PlaygroundRequest(
        use_case_id=use_case.id,
        prompt=payload.prompt,
        response=response_text,
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    audit.log(
        db,
        action="playground.asked",
        summary=f'Prompt run against "{use_case.name}"',
        entity_type="use_case",
        entity_id=use_case.id,
    )

    return _request_out(request, use_case.name)


@router.get("/playground/history", response_model=List[schemas.PlaygroundRequestOut])
def get_playground_history(use_case_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.PlaygroundRequest)
    if use_case_id is not None:
        query = query.filter(models.PlaygroundRequest.use_case_id == use_case_id)
    requests = query.order_by(models.PlaygroundRequest.id.desc()).all()

    use_case_names = {uc.id: uc.name for uc in db.query(models.AIUseCase).all()}
    return [_request_out(r, use_case_names.get(r.use_case_id, "Unknown use case")) for r in requests]
