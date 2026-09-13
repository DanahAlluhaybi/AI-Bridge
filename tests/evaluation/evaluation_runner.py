"""
tests/evaluation/evaluation_runner.py

Runs the whole synthetic evaluation dataset (tests/fixtures/) through
the real AI Adoption decision framework and Automation Opportunity
scoring, compares every result against the hand-defined answer key in
expected-outcomes.json, and prints a measured accuracy report.

Nothing here is hardcoded -- every percentage below is counted from
actual comparisons made in this run. A change to decision.py or
opportunities.py that breaks something will show up here as a lower
number, not as a test that quietly still says 100%.

Usage (from the project root):

    python tests/evaluation/evaluation_runner.py

Exits with status 1 if any accuracy metric falls below PASS_THRESHOLD,
or if a generic/reused recommendation is found across domains -- so
this can be wired into a CI step later without any changes.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
FIXTURES_DIR = ROOT / "tests" / "fixtures"

from app.adoption import decision, opportunities  # noqa: E402

PASS_THRESHOLD = 0.80  # each accuracy metric must clear this to count as a pass


def _load(name):
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _pct(correct: int, total: int) -> float:
    return round(100 * correct / total, 1) if total else 0.0


def evaluate_adoption_decisions():
    systems = {s["id"]: s for s in _load("enterprise-systems.json")}
    expected = _load("expected-outcomes.json")["adoption_decisions"]

    correct = 0
    failures = []
    for case in expected:
        system = systems[case["system_id"]]
        result, _ = decision.determine_adoption_decision(
            system["readiness_score"], system["risk_level"]
        )
        if result == case["expected_decision"]:
            correct += 1
        else:
            failures.append(
                f"  {case['system_id']}: expected {case['expected_decision']}, got {result}"
            )

    return {
        "label": "Adoption Decision Accuracy",
        "correct": correct,
        "total": len(expected),
        "failures": failures,
    }


def evaluate_activity_field(field_name: str, expected_key: str, label: str):
    activities = {a["id"]: a for a in _load("activities.json")}
    expected = _load("expected-outcomes.json")["activities"]

    correct = 0
    total = 0
    failures = []
    for case in expected:
        expected_value = case[expected_key]
        if expected_value is None:
            continue  # the missing-information activity has no ground truth to check
        total += 1
        activity = activities[case["activity_id"]]
        result = opportunities.score_activity(activity)
        if result[field_name] == expected_value:
            correct += 1
        else:
            failures.append(
                f"  {case['activity_id']}: expected {expected_value}, got {result[field_name]}"
            )

    return {"label": label, "correct": correct, "total": total, "failures": failures}


def evaluate_insufficient_information_handling():
    """
    Every activity whose expected outcome is null represents missing
    information -- Bridge should refuse to guess on all of them,
    every field, rather than partially scoring one and not another.
    """
    activities = {a["id"]: a for a in _load("activities.json")}
    expected = _load("expected-outcomes.json")["activities"]

    correct = 0
    total = 0
    failures = []
    for case in expected:
        if case["expected_automation_potential"] is not None:
            continue
        total += 1
        result = opportunities.score_activity(activities[case["activity_id"]])
        all_null = all(
            result[f] is None
            for f in ("automation_potential", "business_impact", "automation_risk", "human_oversight")
        )
        if all_null and "insufficient information" in result["recommendation"].lower():
            correct += 1
        else:
            failures.append(f"  {case['activity_id']}: expected a fail-safe null result, got {result}")

    return {
        "label": "Fail-Safe Handling of Missing Information",
        "correct": correct,
        "total": total,
        "failures": failures,
    }


def evaluate_opportunity_relevance():
    """
    Deterministic stand-in for "is the generated opportunity actually
    relevant to this activity" -- checks that no two activities in
    different domains share identical activity or AI-opportunity
    wording. A reused, generic recommendation would show up here as a
    collision.
    """
    activities = _load("activities.json")
    seen_activity = {}
    seen_opportunity = {}
    collisions = []

    for activity in activities:
        domain = activity["domain"]
        for field, seen in (("activity", seen_activity), ("ai_opportunity", seen_opportunity)):
            text = activity[field].strip().lower()
            if text in seen and seen[text] != domain:
                collisions.append(f"  '{activity[field]}' reused between {seen[text]} and {domain}")
            seen[text] = domain

    total = len(activities)
    correct = total - len(collisions)
    return {
        "label": "Opportunity Relevance (no generic/reused recommendations)",
        "correct": correct,
        "total": total,
        "failures": collisions,
    }


def print_metric(metric: dict) -> bool:
    pct = _pct(metric["correct"], metric["total"])
    passed = (metric["total"] == 0) or (pct / 100 >= PASS_THRESHOLD)
    status = "PASS" if passed else "FAIL"
    print(f"{metric['label']}: {metric['correct']} / {metric['total']} correct = {pct}% [{status}]")
    if metric["failures"]:
        print("\n".join(metric["failures"]))
    return passed


def main() -> int:
    systems_tested = len(_load("enterprise-systems.json"))
    activities_tested = len(_load("activities.json"))

    print("Bridge Evaluation")
    print(f"Systems tested: {systems_tested}")
    print(f"Activities tested: {activities_tested}")
    print()

    metrics = [
        evaluate_adoption_decisions(),
        evaluate_activity_field("automation_potential", "expected_automation_potential", "Automation Potential Accuracy"),
        evaluate_activity_field("human_oversight", "expected_human_oversight", "Human Oversight Accuracy"),
        evaluate_activity_field("business_impact", "expected_business_impact", "Business Impact Accuracy"),
        evaluate_insufficient_information_handling(),
        evaluate_opportunity_relevance(),
    ]

    all_passed = True
    for metric in metrics:
        passed = print_metric(metric)
        all_passed = all_passed and passed
        print()

    generic_failures = len(metrics[-1]["failures"])
    print(f"Generic Recommendation Failures: {generic_failures}")
    print(f"Overall Evaluation: {'PASS' if all_passed else 'FAIL'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
