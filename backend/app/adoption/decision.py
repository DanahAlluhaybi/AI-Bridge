"""
adoption/decision.py

Turns a system's Readiness Score + Risk Level into one AI Adoption
Decision: is this system actually a good candidate to put AI to work
on right now, or not, and why.

This is a decision layer on top of two things AI Bridge already
computes (readiness/engine.py, risk/engine.py) -- it takes plain
values in, not a database session, and runs no scoring of its own.
Thresholds live in one place here rather than scattered through the
logic below, so "how ready is ready enough" stays a one-line change.
"""

from typing import Optional, Tuple

# A system needs at least this Readiness Score before AI adoption is
# considered at all, regardless of risk.
READINESS_MINIMUM = 60

# At or above this Readiness Score a system counts as genuinely
# "ready" -- risk level is what decides the outcome from here, not
# more readiness work.
READINESS_READY = 75

GOOD_CANDIDATE = "Good Candidate"
CONDITIONAL = "Conditional"
NOT_YET = "Not Yet"
NOT_RECOMMENDED = "Not Recommended"
INSUFFICIENT_INFORMATION = "Insufficient Information"

REASONS = {
    GOOD_CANDIDATE: "Ready for AI adoption with standard controls.",
    CONDITIONAL: "Suitable for AI with defined human oversight and additional controls.",
    NOT_YET: "Improve system and data readiness before introducing AI.",
    NOT_RECOMMENDED: "Address identified risks before proceeding with AI automation.",
    INSUFFICIENT_INFORMATION: (
        "This system needs a Readiness and Risk assessment before an "
        "AI Adoption decision can be made."
    ),
}

# Only used to rank systems on the AI Adoption Overview page -- higher
# is a better adoption candidate. Never shown to the user directly.
DECISION_RANK = {
    GOOD_CANDIDATE: 4,
    CONDITIONAL: 3,
    NOT_YET: 2,
    NOT_RECOMMENDED: 1,
    INSUFFICIENT_INFORMATION: 0,
}


def determine_adoption_decision(
    readiness_score: Optional[int], risk_level: Optional[str]
) -> Tuple[str, str]:
    """
    Returns (decision, reason).

    Risk is checked before readiness on purpose: a Critical-risk
    system should never read as "ready" no matter how clean its data
    is. Below that, a readiness floor gates everything else -- a
    system that isn't ready yet stays "Not Yet" regardless of risk.
    Only once a system clears both checks does risk level decide
    between Good Candidate and Conditional.
    """
    if readiness_score is None or risk_level is None:
        return INSUFFICIENT_INFORMATION, REASONS[INSUFFICIENT_INFORMATION]

    if risk_level == "Critical":
        return NOT_RECOMMENDED, REASONS[NOT_RECOMMENDED]

    if readiness_score < READINESS_MINIMUM:
        return NOT_YET, REASONS[NOT_YET]

    is_ready = readiness_score >= READINESS_READY

    if risk_level == "High":
        return (CONDITIONAL, REASONS[CONDITIONAL]) if is_ready else (NOT_RECOMMENDED, REASONS[NOT_RECOMMENDED])

    if risk_level == "Medium":
        return (CONDITIONAL, REASONS[CONDITIONAL]) if is_ready else (NOT_YET, REASONS[NOT_YET])

    # risk_level == "Low"
    return (GOOD_CANDIDATE, REASONS[GOOD_CANDIDATE]) if is_ready else (NOT_YET, REASONS[NOT_YET])
