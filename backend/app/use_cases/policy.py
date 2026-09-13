"""
use_cases/policy.py

The AI Governance policy layer: turns a use case's requested
automation level, together with its system's current Risk Level and
AI Adoption decision, into one of three outcomes -- ALLOW,
HUMAN_APPROVAL, or BLOCK. This is the "policy" the original project
roadmap called a Governance Gateway; AI Adoption (Phase 6) answers
"should this system use AI at all", and this answers the narrower
question "should this SPECIFIC proposed use go ahead, and does a
human need to sign off first".

Pure function, no database access -- same design as
adoption/decision.py, which this deliberately mirrors.
"""

from typing import Optional, Tuple

ALLOW = "ALLOW"
HUMAN_APPROVAL = "HUMAN_APPROVAL"
BLOCK = "BLOCK"

REASONS = {
    ALLOW: "Within acceptable risk for the requested automation level -- no human sign-off required.",
    HUMAN_APPROVAL: "This use case needs a human decision before it can go ahead.",
    BLOCK: "Risk is too high for this use case to proceed, regardless of automation level.",
}

MISSING_RISK_REASON = (
    "This system hasn't been risk-assessed yet -- a human needs to review "
    "this use case before it can proceed."
)


def determine_policy(
    automation_level: str, risk_level: Optional[str], adoption_decision: str
) -> Tuple[str, str]:
    """
    Returns (policy_decision, reason).

    Risk and the Adoption decision are checked before automation level
    -- a Critical-risk system, or one Adoption already flagged as Not
    Recommended, blocks any use case outright. From there, the
    requested automation level decides how much scrutiny is needed:
    Full automation needs a clean risk/readiness picture to pass
    without review, Assisted needs only High risk to trigger one, and
    Advisory (AI suggests, a human always acts) never needs one on
    risk grounds alone.
    """
    if risk_level is None:
        return HUMAN_APPROVAL, MISSING_RISK_REASON

    if risk_level == "Critical" or adoption_decision == "Not Recommended":
        return BLOCK, REASONS[BLOCK]

    if automation_level == "Full":
        if risk_level in ("Medium", "High") or adoption_decision in ("Conditional", "Not Yet"):
            return HUMAN_APPROVAL, REASONS[HUMAN_APPROVAL]
        return ALLOW, REASONS[ALLOW]

    if automation_level == "Assisted":
        if risk_level == "High":
            return HUMAN_APPROVAL, REASONS[HUMAN_APPROVAL]
        return ALLOW, REASONS[ALLOW]

    # Advisory -- AI only ever suggests here, a human always acts on it.
    return ALLOW, REASONS[ALLOW]


# Maps a policy decision straight to the use case's resulting status --
# ALLOW and BLOCK are decided immediately with no human in the loop;
# HUMAN_APPROVAL leaves it Proposed until someone decides in the
# Approval Center.
STATUS_FOR_POLICY = {
    ALLOW: "Approved",
    BLOCK: "Rejected",
    HUMAN_APPROVAL: "Proposed",
}
