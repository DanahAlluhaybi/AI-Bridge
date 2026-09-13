"""
tests/adoption/test_adoption_decision.py

Unit tests for backend/app/adoption/decision.py -- the Readiness +
Risk -> AI Adoption Decision framework. Covers the five scenarios this
feature was specified against, plus the edge cases called out
separately: high readiness + high risk, low readiness + low risk, and
missing information.

Run directly (`python tests/adoption/test_adoption_decision.py`) or via
`python -m unittest tests.adoption.test_adoption_decision` from the
project root -- both work the same way.
"""

import sys
import unittest
from pathlib import Path

# backend/app is a plain package (no FastAPI/SQLAlchemy import at this
# level), so putting backend/ on sys.path is all that's needed --
# nothing here requires the app to actually be running.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.adoption import decision  # noqa: E402


class AdoptionDecisionTests(unittest.TestCase):
    def test_high_readiness_low_risk_is_good_candidate(self):
        result, _ = decision.determine_adoption_decision(95, "Low")
        self.assertEqual(result, decision.GOOD_CANDIDATE)

    def test_high_readiness_medium_risk_is_conditional(self):
        result, _ = decision.determine_adoption_decision(85, "Medium")
        self.assertEqual(result, decision.CONDITIONAL)

    def test_moderate_readiness_low_risk_is_not_yet(self):
        result, _ = decision.determine_adoption_decision(55, "Low")
        self.assertEqual(result, decision.NOT_YET)

    def test_low_readiness_high_risk_is_not_ready_either_way(self):
        # The spec accepts either Not Yet or Not Recommended here --
        # what matters is that it's never a positive decision.
        result, _ = decision.determine_adoption_decision(40, "High")
        self.assertIn(result, (decision.NOT_YET, decision.NOT_RECOMMENDED))

    def test_high_readiness_critical_risk_is_not_recommended(self):
        result, _ = decision.determine_adoption_decision(90, "Critical")
        self.assertEqual(result, decision.NOT_RECOMMENDED)

    def test_critical_risk_overrides_high_readiness(self):
        # Same readiness score as the Good Candidate case above --
        # only the risk level differs, and it should completely change
        # the outcome.
        good, _ = decision.determine_adoption_decision(95, "Low")
        blocked, _ = decision.determine_adoption_decision(95, "Critical")
        self.assertEqual(good, decision.GOOD_CANDIDATE)
        self.assertEqual(blocked, decision.NOT_RECOMMENDED)

    def test_edge_case_high_readiness_high_risk_is_conditional_not_good(self):
        """
        Technically ready, but High risk means it should never come
        back as an unconditional Good Candidate.
        """
        result, _ = decision.determine_adoption_decision(90, "High")
        self.assertNotEqual(result, decision.GOOD_CANDIDATE)
        self.assertEqual(result, decision.CONDITIONAL)

    def test_edge_case_low_readiness_low_risk_is_still_not_yet(self):
        """
        Low risk alone never overrides a readiness floor -- being safe
        to automate isn't the same as the system being ready.
        """
        result, _ = decision.determine_adoption_decision(50, "Low")
        self.assertEqual(result, decision.NOT_YET)

    def test_missing_readiness_is_insufficient_information(self):
        result, _ = decision.determine_adoption_decision(None, "Low")
        self.assertEqual(result, decision.INSUFFICIENT_INFORMATION)

    def test_missing_risk_is_insufficient_information(self):
        result, _ = decision.determine_adoption_decision(80, None)
        self.assertEqual(result, decision.INSUFFICIENT_INFORMATION)

    def test_missing_both_is_insufficient_information(self):
        result, _ = decision.determine_adoption_decision(None, None)
        self.assertEqual(result, decision.INSUFFICIENT_INFORMATION)

    def test_reason_is_never_empty(self):
        for readiness, risk in [(95, "Low"), (40, "High"), (None, None)]:
            _, reason = decision.determine_adoption_decision(readiness, risk)
            self.assertTrue(reason)

    def test_readiness_just_below_ready_threshold_with_low_risk_is_not_yet(self):
        result, _ = decision.determine_adoption_decision(decision.READINESS_READY - 1, "Low")
        self.assertEqual(result, decision.NOT_YET)

    def test_readiness_at_ready_threshold_with_low_risk_is_good_candidate(self):
        result, _ = decision.determine_adoption_decision(decision.READINESS_READY, "Low")
        self.assertEqual(result, decision.GOOD_CANDIDATE)

    def test_readiness_just_below_minimum_is_not_yet_regardless_of_risk(self):
        result, _ = decision.determine_adoption_decision(decision.READINESS_MINIMUM - 1, "Low")
        self.assertEqual(result, decision.NOT_YET)


if __name__ == "__main__":
    unittest.main()
