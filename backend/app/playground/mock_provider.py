"""
playground/mock_provider.py

MockAIProvider -- a free, deterministic stand-in for a real AI model,
used only by the AI Playground demo (Phase 10). The same prompt always
produces the same response for a given use case; nothing here calls
out to any real model or API, so the Playground costs nothing and
needs no API key. A later, optional CloudAIProvider could implement
the same generate_response() signature against a real model without
anything else in this file -- or anything calling it -- changing.
"""

import hashlib

PROVIDER_LABEL = "MockAIProvider — Development Mode"

_TEMPLATES = [
    'Draft response to "{prompt_summary}": here is a suggested first pass. Review before using it in production.',
    'Suggested next step for "{prompt_summary}": break it into smaller, individually reviewable actions rather than one automatic decision.',
    'Summary of "{prompt_summary}": a few fields look worth a closer look before this goes further.',
    'For "{prompt_summary}", a routine, low-risk case like this usually needs only a light review before proceeding.',
]


def generate_response(prompt: str, use_case_name: str) -> str:
    """
    Deterministic by design: hashing the prompt (rather than anything
    random) picks the template, so the same input always reproduces
    the same output -- there's no real model here to vary.
    """
    summary = prompt.strip()
    if len(summary) > 80:
        summary = summary[:77] + "..."

    index = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest(), 16) % len(_TEMPLATES)
    body = _TEMPLATES[index].format(prompt_summary=summary)
    return f"[{PROVIDER_LABEL}] ({use_case_name}) {body}"
