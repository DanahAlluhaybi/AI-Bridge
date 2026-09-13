"""
adoption/opportunities.py

Turns one recorded employee activity into an Automation Opportunity:
how automatable it is, how much it matters, how risky automating it
would be, how much human oversight it still needs, and a priority
number for ranking opportunities against each other.

Every function here takes a plain dict (the shape stored on
SystemActivity, seeded in seed_data.py, and used by the test fixtures
under tests/fixtures/) and is pure -- no database, no FastAPI, nothing
random -- the same rule risk/factors.py follows, so this can be tested
and reasoned about entirely on its own.
"""

from typing import Dict, Optional

LEVELS = ("Low", "Medium", "High")

AUTOMATION_HIGH = "High"
AUTOMATION_MEDIUM = "Medium"
AUTOMATION_LOW = "Low"

OVERSIGHT_REQUIRED = "Required"
OVERSIGHT_RECOMMENDED = "Recommended"
OVERSIGHT_NOT_REQUIRED = "Not required"

INSUFFICIENT_INFORMATION_MESSAGE = (
    "Insufficient information — additional process or activity detail is "
    "required before recommending AI automation."
)

# Every one of these has to be a recognized Low/Medium/High value
# before an activity can be scored at all.
REQUIRED_FIELDS = (
    "frequency",
    "volume",
    "manual_effort",
    "human_judgment",
    "data_sensitivity",
    "process_standardization",
)


def is_activity_complete(activity: Dict) -> bool:
    """
    Whether an activity carries enough information to score. Bridge
    would rather say so plainly than guess -- see score_activity's
    fallback below.
    """
    return all(activity.get(field) in LEVELS for field in REQUIRED_FIELDS)


def score_automation_potential(activity: Dict) -> str:
    """
    High = repetitive, standardized, manual work with little judgment
    involved. Heavy human judgment caps this at Low no matter how
    repetitive the task looks on paper -- repeating a judgment call
    often enough doesn't make it safe to hand to a machine.
    """
    judgment = activity["human_judgment"]
    if judgment == "High":
        return AUTOMATION_LOW

    strong_signals = sum(
        1
        for field in ("frequency", "manual_effort", "process_standardization")
        if activity[field] == "High"
    )

    if judgment == "Medium":
        # Some judgment is involved -- every other signal needs to be
        # strong before this still counts as a high-potential candidate.
        if strong_signals >= 3:
            return AUTOMATION_HIGH
        if strong_signals >= 1:
            return AUTOMATION_MEDIUM
        return AUTOMATION_LOW

    # judgment == "Low"
    if strong_signals >= 2:
        return AUTOMATION_HIGH
    if strong_signals >= 1:
        return AUTOMATION_MEDIUM
    return AUTOMATION_LOW


def score_business_impact(activity: Dict) -> str:
    """High = affects a lot of work, a lot of the time."""
    strong_signals = sum(
        1 for field in ("volume", "frequency", "manual_effort") if activity[field] == "High"
    )
    if strong_signals >= 2:
        return "High"
    if strong_signals >= 1:
        return "Medium"
    return "Low"


def score_automation_risk(activity: Dict) -> str:
    """
    The risk of automating THIS activity -- separate from the parent
    system's own AI Risk Score. Sensitive data or heavy judgment is
    each, on its own, enough to call this risky to hand fully to AI.
    """
    if activity["data_sensitivity"] == "High" or activity["human_judgment"] == "High":
        return "High"
    if activity["data_sensitivity"] == "Medium" or activity["human_judgment"] == "Medium":
        return "Medium"
    return "Low"


def determine_human_oversight(activity: Dict, automation_risk: str) -> str:
    if activity["human_judgment"] == "High" or automation_risk == "High":
        return OVERSIGHT_REQUIRED
    if activity["human_judgment"] == "Medium" or automation_risk == "Medium":
        return OVERSIGHT_RECOMMENDED
    return OVERSIGHT_NOT_REQUIRED


_LEVEL_VALUE = {"Low": 1, "Medium": 2, "High": 3}
_OVERSIGHT_VALUE = {OVERSIGHT_REQUIRED: 3, OVERSIGHT_RECOMMENDED: 2, OVERSIGHT_NOT_REQUIRED: 1}

# Weights for ranking opportunities against EACH OTHER -- not a 0-100
# score shown to the user, just what decides "what to automate first".
# Automation potential and business impact push an opportunity up the
# list; automation risk and how much oversight it still needs pull it
# back down.
PRIORITY_WEIGHTS = {
    "automation_potential": 4,
    "business_impact": 3,
    "automation_risk": -2,
    "human_oversight": -1,
}


def compute_priority_score(
    automation_potential: str, business_impact: str, automation_risk: str, human_oversight: str
) -> int:
    return (
        _LEVEL_VALUE[automation_potential] * PRIORITY_WEIGHTS["automation_potential"]
        + _LEVEL_VALUE[business_impact] * PRIORITY_WEIGHTS["business_impact"]
        + _LEVEL_VALUE[automation_risk] * PRIORITY_WEIGHTS["automation_risk"]
        + _OVERSIGHT_VALUE[human_oversight] * PRIORITY_WEIGHTS["human_oversight"]
    )


def build_recommendation(automation_potential: str, human_oversight: str) -> str:
    if automation_potential == AUTOMATION_HIGH:
        base = (
            "Strong automation candidate — repetitive, standardized work "
            "with limited judgment involved."
        )
    elif automation_potential == AUTOMATION_MEDIUM:
        base = (
            "Partial automation candidate — AI can assist, but some judgment "
            "or variation in the process remains."
        )
    else:
        base = (
            "Limited automation potential — this activity involves meaningful "
            "human judgment or an inconsistent process."
        )

    if human_oversight == OVERSIGHT_REQUIRED:
        return f"{base} Human review is required before acting on any AI output."
    if human_oversight == OVERSIGHT_RECOMMENDED:
        return f"{base} Human spot-checks are recommended."
    return base


def score_activity(activity: Dict) -> Dict[str, Optional[object]]:
    """
    Runs one activity through every function above and returns the
    full result as a plain dict -- the shape routers/adoption.py turns
    into an AutomationOpportunityOut, and the shape
    tests/evaluation/evaluation_runner.py compares against the golden
    dataset.
    """
    if not is_activity_complete(activity):
        return {
            "automation_potential": None,
            "business_impact": None,
            "automation_risk": None,
            "human_oversight": None,
            "priority_score": None,
            "recommendation": INSUFFICIENT_INFORMATION_MESSAGE,
        }

    automation_potential = score_automation_potential(activity)
    business_impact = score_business_impact(activity)
    automation_risk = score_automation_risk(activity)
    human_oversight = determine_human_oversight(activity, automation_risk)
    priority_score = compute_priority_score(
        automation_potential, business_impact, automation_risk, human_oversight
    )
    recommendation = build_recommendation(automation_potential, human_oversight)

    return {
        "automation_potential": automation_potential,
        "business_impact": business_impact,
        "automation_risk": automation_risk,
        "human_oversight": human_oversight,
        "priority_score": priority_score,
        "recommendation": recommendation,
    }
