"""
adapter/validate.py

Step 2: look at the raw records, before any cleanup happens, and
record what's wrong with them. Validation only reports; fixing happens
in normalize.py. Keeping "notice the problem" and "fix the problem" as
separate steps keeps each one easy to read and test on its own.

Phone/date/amount format problems are checked in normalize.py instead
of here, at the point where conversion is actually attempted -- one
field, one place that decides whether it's valid, so the same bad
value is never reported twice from two different checks.
"""

from typing import Any, Dict, List, Set, Tuple

REQUIRED_FIELDS = ["full_name", "city"]
EMPTY_MARKERS = {"", "-", "n/a", "na", "none", "null"}


def is_empty(value: Any) -> bool:
    """True for None and for the placeholder spellings real exports use for "no value"."""
    if value is None:
        return True
    return str(value).strip().lower() in EMPTY_MARKERS


def find_duplicate_keys(records: List[Dict[str, Any]]) -> Set[int]:
    """
    A record counts as a duplicate of an earlier one if it repeats the
    same record_id, or repeats the same (full_name, city, phone)
    combination. Returns the set of record indexes that are repeats
    (never the first occurrence).
    """
    seen_ids: Dict[str, int] = {}
    seen_composite: Dict[Tuple[str, str, str], int] = {}
    duplicate_indexes: Set[int] = set()

    for i, record in enumerate(records):
        record_id = str(record.get("record_id", "")).strip()
        composite = (
            str(record.get("full_name", "")).strip().lower(),
            str(record.get("city", "")).strip().lower(),
            str(record.get("phone", "")).strip(),
        )

        if record_id and record_id in seen_ids:
            duplicate_indexes.add(i)
        elif record_id:
            seen_ids[record_id] = i

        if composite != ("", "", "") and composite in seen_composite:
            duplicate_indexes.add(i)
        elif composite != ("", "", ""):
            seen_composite[composite] = i

    return duplicate_indexes


def validate_email(value: str) -> bool:
    """
    Deliberately simple: one '@', something on both sides, a '.' in
    the domain, no spaces. Not a full RFC 5322 parser.
    """
    value = value.strip()
    if is_empty(value):
        return True  # emptiness is a separate Missing Value issue, not an invalid format
    if value.count("@") != 1 or " " in value:
        return False
    local, _, domain = value.partition("@")
    return bool(local) and "." in domain and not domain.startswith(".")


def validate_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Runs every raw record through the checks above and returns a flat
    list of issue dicts, each shaped like the DetectedIssue model's
    columns (minus job_id, which the pipeline adds):
        {record_index, issue_type, field_name, description, severity}
    """
    issues: List[Dict[str, Any]] = []
    duplicate_indexes = find_duplicate_keys(records)

    for i, record in enumerate(records):
        for field in REQUIRED_FIELDS:
            if is_empty(record.get(field)):
                issues.append({
                    "record_index": i,
                    "issue_type": "Missing Value",
                    "field_name": field,
                    "description": f"Required field '{field}' is missing.",
                    "severity": "Warning",
                })

        email = str(record.get("email", ""))
        if not validate_email(email):
            issues.append({
                "record_index": i,
                "issue_type": "Invalid Format",
                "field_name": "email",
                "description": f"'{email}' does not look like a valid email address.",
                "severity": "Warning",
            })

        if i in duplicate_indexes:
            issues.append({
                "record_index": i,
                "issue_type": "Duplicate Record",
                "field_name": None,
                "description": "This record appears to duplicate an earlier one in the same source.",
                "severity": "Warning",
            })

    return issues
