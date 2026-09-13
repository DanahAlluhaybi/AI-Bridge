"""
tests/automation/test_human_oversight.py

Unit tests for how backend/app/adoption/opportunities.py decides human
oversight -- the part of AI Adoption that keeps Bridge from ever
recommending full, unsupervised automation for sensitive or
judgment-heavy work.

Run directly or via `python -m unittest tests.automation.test_human_oversight`.
"""

import json
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "backend"))

from app.adoption import opportunities  # noqa: E402

FIXTURES_DIR = _ROOT / "tests" / "fixtures"


def _load(name):
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class HumanOversightTests(unittest.TestCase):
    def test_sensitive_data_with_high_automation_potential_still_requires_oversight(self):
        """
        AI may assist a lot here, but sensitive data means oversight
        stays mandatory -- automation potential and oversight are
        answers to two different questions.
        """
        activity = dict(
            frequency="High", volume="High", manual_effort="High",
            human_judgment="Low", data_sensitivity="High", process_standardization="High",
        )
        self.assertEqual(opportunities.score_automation_potential(activity), "High")
        risk = opportunities.score_automation_risk(activity)
        self.assertEqual(opportunities.determine_human_oversight(activity, risk), "Required")

    def test_high_impact_decision_never_gets_full_automation(self):
        activity = dict(
            frequency="Low", volume="Low", manual_effort="Low",
            human_judgment="High", data_sensitivity="Medium", process_standardization="Low",
        )
        risk = opportunities.score_automation_risk(activity)
        oversight = opportunities.determine_human_oversight(activity, risk)
        self.assertEqual(oversight, "Required")

    def test_low_everything_needs_no_oversight(self):
        activity = dict(
            frequency="Low", volume="Low", manual_effort="Low",
            human_judgment="Low", data_sensitivity="Low", process_standardization="Low",
        )
        risk = opportunities.score_automation_risk(activity)
        self.assertEqual(opportunities.determine_human_oversight(activity, risk), "Not required")

    def test_missing_information_never_produces_a_confident_recommendation(self):
        """
        Bridge should fail safely: an incomplete activity comes back
        with every scored field null and a plain 'more information
        needed' message, never a confident 'automate this' answer.
        """
        incomplete = dict(frequency="High", volume="High")  # missing required fields
        result = opportunities.score_activity(incomplete)
        self.assertIsNone(result["automation_potential"])
        self.assertIsNone(result["human_oversight"])
        self.assertIn("insufficient information", result["recommendation"].lower())

    def test_human_oversight_matches_expected_across_fixtures(self):
        activities = {a["id"]: a for a in _load("activities.json")}
        expected = {e["activity_id"]: e for e in _load("expected-outcomes.json")["activities"]}
        mismatches = []
        for activity_id, activity in activities.items():
            expected_oversight = expected[activity_id]["expected_human_oversight"]
            if expected_oversight is None:
                continue
            result = opportunities.score_activity(activity)
            if result["human_oversight"] != expected_oversight:
                mismatches.append(
                    f"{activity_id}: expected {expected_oversight}, got {result['human_oversight']}"
                )
        self.assertEqual(mismatches, [], "\n" + "\n".join(mismatches))


if __name__ == "__main__":
    unittest.main()
