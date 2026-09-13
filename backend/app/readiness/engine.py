"""
readiness/engine.py

Turns the eight dimension scores from dimensions.py into one overall
AI Readiness Score, a readiness level, a list of gaps, and a list of
recommendations, then saves all of it as one AIReadinessAssessment row.

Weights, thresholds, and gap/recommendation text are plain data at the
top of this file rather than buried in logic, so any of them can be
changed in one place.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from .. import models
from . import dimensions

# Must add up to 100%. Data Quality / Data Integration / Technical
# Readiness / Security carry the most concrete signal available today
# (real adapter results, real system configuration) and are weighted
# heaviest. Data Availability / Privacy / Governance / Human Oversight
# are real but thinner signals -- Governance and Human Oversight in
# particular are proxies (see dimensions.py).
WEIGHTS: Dict[str, float] = {
    "Data Quality": 0.15,
    "Data Availability": 0.10,
    "Data Integration": 0.15,
    "Technical Readiness": 0.15,
    "Security": 0.15,
    "Privacy": 0.10,
    "Governance": 0.10,
    "Human Oversight": 0.10,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "WEIGHTS must add up to 100%"

# (minimum score, label) -- checked top to bottom, first match wins.
READINESS_THRESHOLDS: List[Tuple[int, str]] = [
    (90, "AI Ready"),
    (75, "Mostly Ready"),
    (50, "Needs Improvement"),
    (0, "Not Ready"),
]

# A dimension scoring below this is "weak" -- one constant shared by
# gaps and recommendations so the two can never disagree.
WEAK_DIMENSION_THRESHOLD = 70

GAP_MESSAGES: Dict[str, str] = {
    "Data Quality": "The last adapter run found unresolved data-quality issues (missing values, bad formats, or duplicates) in this system's data.",
    "Data Availability": "This system's data isn't fully reachable yet — check its connection status and data source configuration.",
    "Data Integration": "This system's integration method makes its data harder to pull on demand than a live API or database would.",
    "Technical Readiness": "This system hasn't been technically proven end-to-end yet — its data pipeline may not have been run, or it isn't consistently connected.",
    "Security": "This system's declared security level is lower than what AI use cases typically require.",
    "Privacy": "Sensitive data was detected, and additional privacy controls are recommended before this data is used with AI.",
    "Governance": "System ownership and AI governance controls need to be defined more formally for this system's data classification.",
    "Human Oversight": "Human review procedures for AI decisions involving this system's data are not yet defined.",
}

RECOMMENDATION_MESSAGES: Dict[str, str] = {
    "Data Quality": "Improve missing-value handling and duplicate detection, and re-run the adapter to confirm the fix.",
    "Data Availability": "Confirm the system's connection status and fill in a concrete data source.",
    "Data Integration": "Consider exposing a standardized API instead of relying on manual file exports.",
    "Technical Readiness": "Run the Legacy-to-AI Adapter for this system and keep its connection status current.",
    "Security": "Strengthen authentication and access controls for this system.",
    "Privacy": "Apply data masking or field-level protections to the sensitive fields this system was found to contain.",
    "Governance": "Define system ownership and AI governance policies formally, especially given this system's data classification.",
    "Human Oversight": "Define human review procedures for high-impact AI use cases involving this system's data.",
}


def level_for_score(overall_score: int) -> str:
    for minimum, label in READINESS_THRESHOLDS:
        if overall_score >= minimum:
            return label
    return "Not Ready"


def _latest_job_for_system(system: models.EnterpriseSystem, db: Session):
    """
    Looks up this system's AdapterSource and its most recent
    ProcessingJob, if either exists. Returns (has_adapter_source,
    job_or_None); dimensions.py itself never needs to know about
    SQLAlchemy models.
    """
    source = (
        db.query(models.AdapterSource)
        .filter(models.AdapterSource.system_id == system.id)
        .first()
    )
    if source is None:
        return False, None

    job = (
        db.query(models.ProcessingJob)
        .filter(models.ProcessingJob.source_id == source.id)
        .order_by(models.ProcessingJob.id.desc())
        .first()
    )
    return True, job


def compute_dimension_scores(system: models.EnterpriseSystem, db: Session) -> Dict[str, int]:
    has_adapter_source, job = _latest_job_for_system(system, db)
    has_adapter_run = job is not None

    if job is not None and job.records_processed:
        sensitive_count = (job.classification_summary or {}).get("Sensitive", 0)
        sensitive_ratio = sensitive_count / job.records_processed
        issues_detected = job.issues_detected
        records_processed = job.records_processed
    else:
        sensitive_ratio = 0.0
        issues_detected = 0
        records_processed = 0

    return {
        "Data Quality": dimensions.score_data_quality(has_adapter_run, issues_detected, records_processed),
        "Data Availability": dimensions.score_data_availability(
            system.status, bool(system.data_source), has_adapter_source
        ),
        "Data Integration": dimensions.score_data_integration(system.integration_type),
        "Technical Readiness": dimensions.score_technical_readiness(
            has_adapter_run, system.integration_type, system.status
        ),
        "Security": dimensions.score_security(system.security_level),
        "Privacy": dimensions.score_privacy(has_adapter_run, sensitive_ratio, system.data_classification),
        "Governance": dimensions.score_governance(system.status, system.data_classification),
        "Human Oversight": dimensions.score_human_oversight(system.data_classification),
    }


def compute_overall_score(dimension_scores: Dict[str, int]) -> int:
    weighted = sum(dimension_scores[name] * weight for name, weight in WEIGHTS.items())
    return max(0, min(100, round(weighted)))


def identify_gaps(dimension_scores: Dict[str, int]) -> List[Dict[str, Any]]:
    return [
        {"dimension": name, "score": score, "description": GAP_MESSAGES[name]}
        for name, score in dimension_scores.items()
        if score < WEAK_DIMENSION_THRESHOLD
    ]


def generate_recommendations(dimension_scores: Dict[str, int]) -> List[str]:
    return [
        RECOMMENDATION_MESSAGES[name]
        for name, score in dimension_scores.items()
        if score < WEAK_DIMENSION_THRESHOLD
    ]


def run_assessment(system: models.EnterpriseSystem, db: Session) -> models.AIReadinessAssessment:
    """
    Computes everything above and saves it as a new row. Assessments
    are a history, not a single current value -- running this again
    for the same system adds a row rather than overwriting the last one.
    """
    dimension_scores = compute_dimension_scores(system, db)
    overall_score = compute_overall_score(dimension_scores)
    level = level_for_score(overall_score)

    assessment = models.AIReadinessAssessment(
        system_id=system.id,
        overall_score=overall_score,
        readiness_level=level,
        dimension_scores=dimension_scores,
        identified_gaps=identify_gaps(dimension_scores),
        recommendations=generate_recommendations(dimension_scores),
        created_at=datetime.now(timezone.utc),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment
