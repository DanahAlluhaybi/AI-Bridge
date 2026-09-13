"""
tests/governance/test_mock_provider.py

Unit tests for backend/app/playground/mock_provider.py -- the free,
deterministic stand-in for a real AI model that powers the AI
Playground (Phase 10). What actually matters here isn't any specific
wording, it's the contract every caller relies on: same input always
gives the same output, long prompts don't blow up the response, and
the use case name always shows up so a Playground history list stays
readable.

Run directly (`python tests/governance/test_mock_provider.py`) or via
`python -m unittest tests.governance.test_mock_provider` from the
project root.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from app.playground import mock_provider  # noqa: E402


class GenerateResponseTests(unittest.TestCase):
    def test_same_prompt_and_use_case_gives_identical_response(self):
        first = mock_provider.generate_response("Flag any duplicate invoices", "Invoice Auditor")
        second = mock_provider.generate_response("Flag any duplicate invoices", "Invoice Auditor")
        self.assertEqual(first, second)

    def test_same_prompt_under_a_different_use_case_name_still_labels_correctly(self):
        # The response template picked is a function of the prompt
        # alone -- only the use-case label in the output should change.
        prompt = "Summarize this candidate's resume"
        a = mock_provider.generate_response(prompt, "Resume Screener")
        b = mock_provider.generate_response(prompt, "HR Intake Bot")
        self.assertIn("Resume Screener", a)
        self.assertIn("HR Intake Bot", b)

    def test_response_always_carries_the_provider_label(self):
        response = mock_provider.generate_response("Anything at all", "Some Use Case")
        self.assertIn(mock_provider.PROVIDER_LABEL, response)

    def test_response_always_carries_the_use_case_name(self):
        response = mock_provider.generate_response("Anything at all", "Refund Triage Assistant")
        self.assertIn("Refund Triage Assistant", response)

    def test_long_prompt_is_truncated_in_the_response(self):
        long_prompt = "A" * 500
        response = mock_provider.generate_response(long_prompt, "Stress Test")
        self.assertIn("...", response)
        # The full 500-character prompt should never appear verbatim.
        self.assertNotIn("A" * 500, response)

    def test_short_prompt_is_not_truncated(self):
        response = mock_provider.generate_response("Short prompt", "Quick Case")
        self.assertNotIn("...", response)
        self.assertIn("Short prompt", response)

    def test_empty_prompt_does_not_raise(self):
        # Pydantic's min_length on PlaygroundRequestCreate should catch
        # this before it ever reaches here, but the function itself
        # should still fail safely rather than throw.
        response = mock_provider.generate_response("", "Edge Case")
        self.assertIn(mock_provider.PROVIDER_LABEL, response)

    def test_response_is_deterministic_across_many_distinct_prompts(self):
        # Broad sanity sweep: every prompt in a batch reproduces
        # exactly the same output on a second call.
        prompts = [f"Prompt number {i}" for i in range(25)]
        first_pass = [mock_provider.generate_response(p, "Batch Case") for p in prompts]
        second_pass = [mock_provider.generate_response(p, "Batch Case") for p in prompts]
        self.assertEqual(first_pass, second_pass)


if __name__ == "__main__":
    unittest.main()
