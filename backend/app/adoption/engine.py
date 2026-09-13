"""
adoption/engine.py

Ties decision.py and opportunities.py to the database: for one system,
looks up its latest Readiness and Risk assessments and its recorded
activities, and returns an AI Adoption decision plus a ranked list of
Automation Opportunities. Also builds the company-wide overview used
by the AI Adoption page.

Unlike the Readiness and Risk engines, this never writes a new row --
an AI Adoption decision is a live read of whatever Readiness/Risk
assessments already exist, not a separate thing a user clicks a button
to run. Re-assessing Readiness or Risk automatically changes what
Adoption reports next time, with nothing extra to keep in sync.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .. import models
from . import decision, opportunities


def _latest_readiness_score(system_id: int, db: Session) -> Optional[int]:
    latest = (
        db.query(models.AIReadinessAssessment)
        .filter(models.AIReadinessAssessment.system_id == system_id)
        .order_by(models.AIReadinessAssessment.id.desc())
        .first()
    )
    return latest.overall_score if latest is not None else None


def _latest_risk_level(system_id: int, db: Session) -> Optional[str]:
    latest = (
        db.query(models.AIRiskAssessment)
        .filter(models.AIRiskAssessment.system_id == system_id)
        .order_by(models.AIRiskAssessment.id.desc())
        .first()
    )
    return latest.risk_level if latest is not None else None


def _activity_as_dict(activity: models.SystemActivity) -> Dict[str, Any]:
    return {
        "id": activity.id,
        "system_id": activity.system_id,
        "activity": activity.activity,
        "description": activity.description,
        "ai_opportunity": activity.ai_opportunity,
        "frequency": activity.frequency,
        "volume": activity.volume,
        "manual_effort": activity.manual_effort,
        "human_judgment": activity.human_judgment,
        "data_sensitivity": activity.data_sensitivity,
        "process_standardization": activity.process_standardization,
    }


def get_ranked_opportunities(system_id: int, db: Session) -> List[Dict[str, Any]]:
    """
    Every recorded activity for this system, scored and sorted with
    the best automation candidate first. A missing priority_score
    (an incomplete activity) sorts last rather than crashing the sort.
    """
    activities = (
        db.query(models.SystemActivity)
        .filter(models.SystemActivity.system_id == system_id)
        .order_by(models.SystemActivity.id.asc())
        .all()
    )

    scored = []
    for activity in activities:
        record = _activity_as_dict(activity)
        result = opportunities.score_activity(record)
        scored.append({**record, **result})

    scored.sort(key=lambda item: item["priority_score"] if item["priority_score"] is not None else -999, reverse=True)
    return scored


def get_system_adoption(system: models.EnterpriseSystem, db: Session) -> Dict[str, Any]:
    readiness_score = _latest_readiness_score(system.id, db)
    risk_level = _latest_risk_level(system.id, db)
    adoption_decision, reason = decision.determine_adoption_decision(readiness_score, risk_level)

    return {
        "system_id": system.id,
        "system_name": system.name,
        "readiness_score": readiness_score,
        "risk_level": risk_level,
        "decision": adoption_decision,
        "reason": reason,
        "opportunities": get_ranked_opportunities(system.id, db),
    }


def get_adoption_overview(db: Session) -> List[Dict[str, Any]]:
    """
    One row per system, ranked by adoption suitability (not plain
    readiness) -- Good Candidate systems first, then Conditional, then
    Not Yet, then Not Recommended, then anything still unassessed.
    Systems tied on decision are broken by readiness score.
    """
    systems = db.query(models.EnterpriseSystem).all()

    rows = []
    for system in systems:
        readiness_score = _latest_readiness_score(system.id, db)
        risk_level = _latest_risk_level(system.id, db)
        adoption_decision, _ = decision.determine_adoption_decision(readiness_score, risk_level)

        ranked = get_ranked_opportunities(system.id, db)
        top_opportunity = next((o["activity"] for o in ranked if o["priority_score"] is not None), None)

        rows.append({
            "system_id": system.id,
            "system_name": system.name,
            "readiness_score": readiness_score,
            "risk_level": risk_level,
            "decision": adoption_decision,
            "top_opportunity": top_opportunity,
        })

    rows.sort(
        key=lambda row: (
            decision.DECISION_RANK[row["decision"]],
            row["readiness_score"] if row["readiness_score"] is not None else -1,
        ),
        reverse=True,
    )
    return rows
