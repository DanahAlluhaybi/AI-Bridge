"""
Turns the four risk contributions from factors.py into one overall AI
Risk Score, a risk level, and the list of factors that drove it up,
then saves all of it as one AIRiskAssessment row.

Weights and thresholds are plain data at the top of this file, the
same pattern readiness/engine.py uses, so either can be changed in one
place without touching the scoring logic itself.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from .. import models
from . import factors

# Must add up to 100%. Data Sensitivity and Security Gap are weighted
# heaviest -- both come directly from the system's own declared
# profile, with no dependency on whether it has been assessed yet.
WEIGHTS: Dict[str, float] = {
    "Data Sensitivity": 0.30,
    "Security Gap": 0.25,
    "Readiness Gap": 0.25,
    "Oversight Gap": 0.20,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "WEIGHTS must add up to 100%"

# (minimum score, label) -- checked top to bottom, first match wins.
# Higher score means more risk here, the opposite direction from
# readiness/engine.py's READINESS_THRESHOLDS.
RISK_THRESHOLDS: List[Tuple[int, str]] = [
    (75, "Critical"),
    (50, "High"),
    (25, "Medium"),
    (0, "Low"),
]

# A factor contributing at or above this is worth surfacing to the
# user as a specific reason, not just folded into the overall number.
SIGNIFICANT_FACTOR_THRESHOLD = 60

FACTOR_MESSAGES: Dict[str, str] = {
    "Data Sensitivity": "This system's declared data classification implies significant exposure if AI acts on its data without additional controls.",
    "Security Gap": "This system's declared security level is weaker than AI use cases typically require.",
    "Readiness Gap": "This system is far from AI-ready — its AI Readiness Score is low or it hasn't been assessed yet.",
    "Oversight Gap": "This system's data classification calls for human review procedures that aren't defined yet.",
}


def level_for_score(risk_score: int) -> str:
    for minimum, label in RISK_THRESHOLDS:
        if risk_score >= minimum:
            return label
    return "Low"


def _latest_readiness_score(system: models.EnterpriseSystem, db: Session) -> Optional[int]:
    latest = (
        db.query(models.AIReadinessAssessment)
        .filter(models.AIReadinessAssessment.system_id == system.id)
        .order_by(models.AIReadinessAssessment.id.desc())
        .first()
    )
    return latest.overall_score if latest is not None else None


def compute_risk_factors(system: models.EnterpriseSystem, db: Session) -> Dict[str, int]:
    readiness_score = _latest_readiness_score(system, db)
    return {
        "Data Sensitivity": factors.score_data_sensitivity_risk(system.data_classification),
        "Security Gap": factors.score_security_gap_risk(system.security_level),
        "Readiness Gap": factors.score_readiness_gap_risk(readiness_score),
        "Oversight Gap": factors.score_oversight_gap_risk(system.data_classification),
    }


def compute_overall_risk(risk_factors: Dict[str, int]) -> int:
    weighted = sum(risk_factors[name] * weight for name, weight in WEIGHTS.items())
    return max(0, min(100, round(weighted)))


def identify_risk_drivers(risk_factors: Dict[str, int]) -> List[Dict[str, Any]]:
    return [
        {"factor": name, "score": score, "description": FACTOR_MESSAGES[name]}
        for name, score in risk_factors.items()
        if score >= SIGNIFICANT_FACTOR_THRESHOLD
    ]


def run_risk_assessment(system: models.EnterpriseSystem, db: Session) -> models.AIRiskAssessment:
    """
    Computes everything above and saves it as a new row. Like AI
    Readiness Assessments, this is a history table -- running it again
    for the same system adds a row rather than overwriting the last one.
    """
    risk_factors = compute_risk_factors(system, db)
    risk_score = compute_overall_risk(risk_factors)
    level = level_for_score(risk_score)

    assessment = models.AIRiskAssessment(
        system_id=system.id,
        risk_score=risk_score,
        risk_level=level,
        risk_factors=risk_factors,
        risk_drivers=identify_risk_drivers(risk_factors),
        created_at=datetime.now(timezone.utc),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment
