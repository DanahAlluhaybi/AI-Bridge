"""
routers/adapter.py

Endpoints for the Legacy-to-AI Adapter:

    GET  /api/adapter/sources                       -> list available mock sources
    POST /api/adapter/sources/{source_id}/process    -> run the adapter, return full result
    GET  /api/adapter/jobs                           -> list past processing jobs
    GET  /api/adapter/jobs/{job_id}                  -> one job's summary + results + issues
    GET  /api/adapter/jobs/{job_id}/results          -> just the before/after records
    GET  /api/adapter/jobs/{job_id}/issues           -> just the detected issues

Processing is one endpoint (`POST /sources/{source_id}/process`) that
looks up the source's own type and dispatches internally (see
adapter/extract.py), rather than one endpoint per source type --
validation, normalization, classification, and sensitive-data
detection are identical regardless of input format, so only extraction
needs to branch.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..adapter.pipeline import run_adapter
from ..database import get_db

router = APIRouter()


def _source_out(source: models.AdapterSource, db: Session) -> schemas.AdapterSourceOut:
    system = db.get(models.EnterpriseSystem, source.system_id)
    return schemas.AdapterSourceOut(
        id=source.id,
        system_id=source.system_id,
        system_name=system.name if system else "Unknown system",
        source_type=source.source_type,
        description=source.description,
    )


def _job_detail(job: models.ProcessingJob, db: Session) -> schemas.ProcessingJobDetail:
    results = (
        db.query(models.ProcessingResult)
        .filter(models.ProcessingResult.job_id == job.id)
        .order_by(models.ProcessingResult.record_index)
        .all()
    )
    issues = (
        db.query(models.DetectedIssue)
        .filter(models.DetectedIssue.job_id == job.id)
        .order_by(models.DetectedIssue.record_index)
        .all()
    )
    return schemas.ProcessingJobDetail(
        **schemas.ProcessingJobOut.model_validate(job).model_dump(),
        results=[schemas.ProcessingResultOut.model_validate(r) for r in results],
        issues=[schemas.DetectedIssueOut.model_validate(i) for i in issues],
    )


@router.get("/adapter/sources", response_model=List[schemas.AdapterSourceOut])
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(models.AdapterSource).order_by(models.AdapterSource.id).all()
    return [_source_out(s, db) for s in sources]


@router.post(
    "/adapter/sources/{source_id}/process",
    response_model=schemas.ProcessingJobDetail,
    status_code=201,
)
def process_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(models.AdapterSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    job = run_adapter(source, db)
    return _job_detail(job, db)


@router.get("/adapter/jobs", response_model=List[schemas.ProcessingJobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(models.ProcessingJob).order_by(models.ProcessingJob.id.desc()).all()


@router.get("/adapter/jobs/{job_id}", response_model=schemas.ProcessingJobDetail)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(models.ProcessingJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return _job_detail(job, db)


@router.get("/adapter/jobs/{job_id}/results", response_model=List[schemas.ProcessingResultOut])
def get_job_results(job_id: int, db: Session = Depends(get_db)):
    if db.get(models.ProcessingJob, job_id) is None:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return (
        db.query(models.ProcessingResult)
        .filter(models.ProcessingResult.job_id == job_id)
        .order_by(models.ProcessingResult.record_index)
        .all()
    )


@router.get("/adapter/jobs/{job_id}/issues", response_model=List[schemas.DetectedIssueOut])
def get_job_issues(job_id: int, db: Session = Depends(get_db)):
    if db.get(models.ProcessingJob, job_id) is None:
        raise HTTPException(status_code=404, detail="Processing job not found")
    return (
        db.query(models.DetectedIssue)
        .filter(models.DetectedIssue.job_id == job_id)
        .order_by(models.DetectedIssue.record_index)
        .all()
    )
