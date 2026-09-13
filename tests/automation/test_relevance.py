"""
tests/automation/test_relevance.py

Guards against the failure mode the AI Adoption spec calls out
explicitly: Bridge inventing the same generic automation opportunities
for every system instead of ones actually connected to that system's
own recorded activities. If HR, Supply Chain, and CRM all came back
with the same three "opportunities", something would be badly wrong.

Run directly or via `python -m unittest tests.automation.test_relevance`.
"""

import json
import sys
import unittest
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "backend"))

FIXTURES_DIR = _ROOT / "tests" / "fixtures"


def _load(name):
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


class RelevanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.activities = _load("activities.json")

    def test_each_domain_has_more_than_one_distinct_activity(self):
        by_domain = {}
        for activity in self.activities:
            by_domain.setdefault(activity["domain"], set()).add(activity["activity"])
        for domain, names in by_domain.items():
            self.assertGreater(
                len(names), 1, f"{domain} only has one distinct activity recorded"
            )

    def test_no_activity_text_is_reused_across_different_domains(self):
        """
        The same activity WORDING should never show up under two
        different domains -- that would mean Bridge is reusing
        boilerplate instead of describing what that system's own
        employees actually do.
        """
        seen = {}
        collisions = []
        for activity in self.activities:
            text = activity["activity"].strip().lower()
            if text in seen and seen[text] != activity["domain"]:
                collisions.append((text, seen[text], activity["domain"]))
            seen[text] = activity["domain"]
        self.assertEqual(collisions, [], f"Reused activity text across domains: {collisions}")

    def test_no_ai_opportunity_text_is_reused_across_different_domains(self):
        seen = {}
        collisions = []
        for activity in self.activities:
            text = activity["ai_opportunity"].strip().lower()
            if text in seen and seen[text] != activity["domain"]:
                collisions.append((text, seen[text], activity["domain"]))
            seen[text] = activity["domain"]
        self.assertEqual(collisions, [], f"Reused AI opportunity text across domains: {collisions}")

    def test_domains_do_not_all_produce_the_same_top_recommendation(self):
        """
        A coarse but meaningful check: group activities by domain,
        find each domain's best-word overlap with every other domain's
        activity names. If every domain's activities were worded
        identically, this would flag it.
        """
        by_domain = {}
        for activity in self.activities:
            by_domain.setdefault(activity["domain"], Counter())[activity["activity"]] += 1

        all_activity_sets = [set(counter.keys()) for counter in by_domain.values()]
        for i, first in enumerate(all_activity_sets):
            for second in all_activity_sets[i + 1:]:
                overlap = first & second
                self.assertEqual(
                    overlap, set(), f"Identical activity names shared across domains: {overlap}"
                )


if __name__ == "__main__":
    unittest.main()
