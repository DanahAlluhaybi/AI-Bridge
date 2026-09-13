"""
tests/automation/test_opportunity_detection.py

Unit tests for backend/app/adoption/opportunities.py's automation
potential and business impact scoring. Two kinds of coverage:

1. The exact scenarios called out in the AI Adoption spec (data entry,
   request classification, a high-judgment approval).
2. Every activity in tests/fixtures/activities.json checked against
   its hand-defined answer in tests/fixtures/expected-outcomes.json.

Run directly or via `python -m unittest tests.automation.test_opportunity_detection`.
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


class ExampleScenarioTests(unittest.TestCase):
    """The specific examples the AI Adoption feature was specified against."""

    def test_repetitive_standardized_data_entry_is_high_potential(self):
        activity = dict(
            frequency="High", volume="High", manual_effort="High",
            human_judgment="Low", data_sensitivity="Medium", process_standardization="High",
        )
        self.assertEqual(opportunities.score_automation_potential(activity), "High")

    def test_request_classification_is_high_potential_with_recommended_oversight(self):
        activity = dict(
            frequency="High", volume="High", manual_effort="Medium",
            human_judgment="Low", data_sensitivity="Medium", process_standardization="High",
        )
        potential = opportunities.score_automation_potential(activity)
        risk = opportunities.score_automation_risk(activity)
        oversight = opportunities.determine_human_oversight(activity, risk)
        self.assertEqual(potential, "High")
        self.assertEqual(oversight, "Recommended")

    def test_high_impact_judgment_decision_is_never_high_potential(self):
        """An activity like 'approve employee termination' -- rare,
        low effort, but a real judgment call. Should never come back
        as a strong automation candidate, no matter how it scores on
        the other five fields."""
        activity = dict(
            frequency="Low", volume="Low", manual_effort="Low",
            human_judgment="High", data_sensitivity="High", process_standardization="Medium",
        )
        self.assertIn(opportunities.score_automation_potential(activity), ("Low", "Medium"))
        self.assertNotEqual(opportunities.score_automation_potential(activity), "High")

    def test_high_judgment_forces_required_oversight_even_with_other_low_signals(self):
        activity = dict(
            frequency="Low", volume="Low", manual_effort="Low",
            human_judgment="High", data_sensitivity="Low", process_standardization="Low",
        )
        risk = opportunities.score_automation_risk(activity)
        oversight = opportunities.determine_human_oversight(activity, risk)
        self.assertEqual(oversight, "Required")


class FixtureAccuracyTests(unittest.TestCase):
    """Every synthetic activity, checked against its hand-defined answer."""

    @classmethod
    def setUpClass(cls):
        cls.activities = {a["id"]: a for a in _load("activities.json")}
        cls.expected = {e["activity_id"]: e for e in _load("expected-outcomes.json")["activities"]}

    def test_automation_potential_matches_expected(self):
        mismatches = []
        for activity_id, activity in self.activities.items():
            expected = self.expected[activity_id]["expected_automation_potential"]
            if expected is None:
                continue
            result = opportunities.score_activity(activity)
            if result["automation_potential"] != expected:
                mismatches.append(
                    f"{activity_id}: expected {expected}, got {result['automation_potential']}"
                )
        self.assertEqual(mismatches, [], "\n" + "\n".join(mismatches))

    def test_business_impact_matches_expected(self):
        mismatches = []
        for activity_id, activity in self.activities.items():
            expected = self.expected[activity_id]["expected_business_impact"]
            if expected is None:
                continue
            result = opportunities.score_activity(activity)
            if result["business_impact"] != expected:
                mismatches.append(
                    f"{activity_id}: expected {expected}, got {result['business_impact']}"
                )
        self.assertEqual(mismatches, [], "\n" + "\n".join(mismatches))


if __name__ == "__main__":
    unittest.main()
