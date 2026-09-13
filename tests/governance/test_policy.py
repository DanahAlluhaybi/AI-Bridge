"""
tests/governance/test_policy.py

Unit tests for backend/app/use_cases/policy.py -- the Automation Level
+ Risk + AI Adoption Decision -> ALLOW / HUMAN_APPROVAL / BLOCK policy.
Same style as tests/adoption/test_adoption_decision.py: every branch of
determine_policy() gets its own case, plus the edge cases that matter
most for a governance gate -- missing risk, Critical risk, and a
Not Recommended adoption decision all overriding a lenient automation
level.

Run directly (`python tests/governance/test_policy.py`) or via
`python -m unittest tests.governance.test_policy` from the project
root.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.use_cases import policy  # noqa: E402


class DeterminePolicyTests(unittest.TestCase):
    # -- Advisory: AI only ever suggests, so risk/adoption never block it --
    def test_advisory_is_always_allowed_regardless_of_risk(self):
        for risk in ("Low", "Medium", "High"):
            result, _ = policy.determine_policy("Advisory", risk, "Good Candidate")
            self.assertEqual(result, policy.ALLOW)

    def test_advisory_still_blocked_by_critical_risk(self):
        # Critical risk and Not Recommended are hard stops that apply
        # no matter what the requested automation level is.
        result, _ = policy.determine_policy("Advisory", "Critical", "Good Candidate")
        self.assertEqual(result, policy.BLOCK)

    # -- Assisted: only High risk triggers a human review --
    def test_assisted_low_or_medium_risk_is_allowed(self):
        for risk in ("Low", "Medium"):
            result, _ = policy.determine_policy("Assisted", risk, "Good Candidate")
            self.assertEqual(result, policy.ALLOW)

    def test_assisted_high_risk_needs_human_approval(self):
        result, _ = policy.determine_policy("Assisted", "High", "Good Candidate")
        self.assertEqual(result, policy.HUMAN_APPROVAL)

    # -- Full: needs a clean readiness/risk picture to pass without review --
    def test_full_low_risk_good_candidate_is_allowed(self):
        result, _ = policy.determine_policy("Full", "Low", "Good Candidate")
        self.assertEqual(result, policy.ALLOW)

    def test_full_medium_or_high_risk_needs_human_approval(self):
        for risk in ("Medium", "High"):
            result, _ = policy.determine_policy("Full", risk, "Good Candidate")
            self.assertEqual(result, policy.HUMAN_APPROVAL)

    def test_full_low_risk_but_conditional_or_not_yet_still_needs_approval(self):
        # Clean risk alone isn't enough for Full automation -- the
        # system's own Adoption decision has to be clean too.
        for adoption_decision in ("Conditional", "Not Yet"):
            result, _ = policy.determine_policy("Full", "Low", adoption_decision)
            self.assertEqual(result, policy.HUMAN_APPROVAL)

    # -- Hard stops that override every automation level --
    def test_critical_risk_blocks_every_automation_level(self):
        for level in ("Advisory", "Assisted", "Full"):
            result, _ = policy.determine_policy(level, "Critical", "Good Candidate")
            self.assertEqual(result, policy.BLOCK)

    def test_not_recommended_adoption_blocks_every_automation_level(self):
        for level in ("Advisory", "Assisted", "Full"):
            result, _ = policy.determine_policy(level, "Low", "Not Recommended")
            self.assertEqual(result, policy.BLOCK)

    # -- Missing information is a fail-safe, not a guess --
    def test_missing_risk_always_needs_human_approval(self):
        for level in ("Advisory", "Assisted", "Full"):
            result, reason = policy.determine_policy(level, None, "Insufficient Information")
            self.assertEqual(result, policy.HUMAN_APPROVAL)
            self.assertEqual(reason, policy.MISSING_RISK_REASON)

    def test_missing_risk_checked_before_the_critical_shortcut(self):
        # None should never be compared equal to "Critical" -- this
        # would raise or misbehave if the None-check weren't first.
        result, _ = policy.determine_policy("Full", None, "Good Candidate")
        self.assertEqual(result, policy.HUMAN_APPROVAL)

    # -- General shape checks --
    def test_reason_is_never_empty(self):
        for level in ("Advisory", "Assisted", "Full"):
            for risk in (None, "Low", "Medium", "High", "Critical"):
                _, reason = policy.determine_policy(level, risk, "Good Candidate")
                self.assertTrue(reason)

    def test_status_for_policy_covers_every_decision(self):
        for decision_value in (policy.ALLOW, policy.HUMAN_APPROVAL, policy.BLOCK):
            self.assertIn(decision_value, policy.STATUS_FOR_POLICY)

    def test_status_for_policy_maps_to_the_expected_use_case_statuses(self):
        self.assertEqual(policy.STATUS_FOR_POLICY[policy.ALLOW], "Approved")
        self.assertEqual(policy.STATUS_FOR_POLICY[policy.BLOCK], "Rejected")
        self.assertEqual(policy.STATUS_FOR_POLICY[policy.HUMAN_APPROVAL], "Proposed")


if __name__ == "__main__":
    unittest.main()
