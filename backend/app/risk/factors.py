"""
Turns what's known about a system into four 0-100 risk contributions.
Unlike readiness/dimensions.py, higher here means MORE risk, not more
ready -- a system with weak security and no readiness assessment yet
should score high risk, not a neutral middle value.

Every function is pure and dependency-free: same inputs, same output,
no AI model call, nothing random, no database or FastAPI import. That
also makes each one straightforward to test in isolation.
"""

from typing import Optional

from ..readiness.dimensions import score_human_oversight

_CLASSIFICATION_RISK = {"Public": 5, "Internal": 25, "Confidential": 60, "Restricted": 90}
_SECURITY_RISK = {"Critical": 5, "High": 20, "Medium": 45, "Low": 75}


def _clamp(score: float) -> int:
    """Every risk contribution is 0-100, always a whole number."""
    return max(0, min(100, round(score)))


def score_data_sensitivity_risk(data_classification: str) -> int:
    """How much exposure this system's declared data classification implies on its own."""
    return _clamp(_CLASSIFICATION_RISK.get(data_classification, 40))


def score_security_gap_risk(security_level: str) -> int:
    """The inverse of the system's declared security level -- weaker security, higher risk."""
    return _clamp(_SECURITY_RISK.get(security_level, 50))


def score_readiness_gap_risk(latest_readiness_score: Optional[int]) -> int:
    """
    How far this system is from being AI-ready, based on its most
    recent AI Readiness Assessment. No assessment yet is treated as a
    neutral, unproven middle -- not automatically low or high risk.
    """
    if latest_readiness_score is None:
        return 50
    return _clamp(100 - latest_readiness_score)


def score_oversight_gap_risk(data_classification: str) -> int:
    """
    How much human review this system's data would need before AI acts
    on it, if none exists yet. Reuses the readiness engine's own Human
    Oversight scoring so the two engines never disagree about what a
    given classification implies -- just read here as a risk (100 -
    oversight readiness) instead of a readiness contribution.
    """
    oversight_readiness = score_human_oversight(data_classification)
    return _clamp(100 - oversight_readiness)
