"""
adapter/normalize.py

Step 3: take one raw record and produce a normalized one -- same
fields, cleaned into one consistent representation. City name variants
("Jeddah" / "جدة" / "JEDDAH") collapse to one canonical spelling, dates
in several formats become YYYY-MM-DD, phone numbers become
+966XXXXXXXXX, and missing-value placeholders ("", "N/A", "-") collapse
into one real empty value.

Each normalizer is a small, independent function so each field's
cleanup logic can be read and tested in isolation.

Dates are parsed with a hand-written regex rather than strptime format
codes like "%-m" (single-digit month) -- those codes aren't supported
by Python's strptime on Windows, and this needs to run identically on
every OS.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

from .validate import is_empty

# Known spelling/language variants for the cities that appear in the
# mock data. Not exhaustive -- an unrecognized city is passed through
# with simple title-casing rather than rejected.
CITY_ALIASES = {
    "jeddah": "Jeddah", "jedda": "Jeddah", "جدة": "Jeddah",
    "riyadh": "Riyadh", "الرياض": "Riyadh",
    "dammam": "Dammam", "الدمام": "Dammam",
    "khobar": "Khobar", "al khobar": "Khobar", "الخبر": "Khobar",
    "makkah": "Makkah", "mecca": "Makkah",
    "jubail": "Jubail",
}

COUNTRY_ALIASES = {
    "ksa": "Saudi Arabia",
    "sa": "Saudi Arabia",
    "saudi arabia": "Saudi Arabia",
    "المملكة العربية السعودية": "Saudi Arabia",
}

# (regex, field order) -- "ymd" means the 3 captured groups are
# (year, month, day); "dmy" means (day, month, year). 1- or 2-digit
# month/day are both accepted.
DATE_PATTERNS = [
    (re.compile(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})$"), "ymd"),
    (re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$"), "dmy"),
]


def normalize_text(value: Any) -> str:
    """Trim outer whitespace and collapse any run of inner whitespace to one space."""
    text = str(value).strip()
    if is_empty(text):
        return ""
    return re.sub(r"\s+", " ", text)


def normalize_city(value: Any) -> str:
    text = str(value).strip()
    if is_empty(text):
        return ""
    return CITY_ALIASES.get(text.lower(), text.title())


def normalize_country(value: Any) -> str:
    text = str(value).strip()
    if is_empty(text):
        return ""
    return COUNTRY_ALIASES.get(text.lower(), text.title())


def normalize_date(value: Any) -> Tuple[str, bool]:
    """
    Returns (normalized_value, was_parseable). Accepts YYYY-M-D,
    YYYY/M/D, D-M-YYYY, and D/M/YYYY, and returns ISO YYYY-MM-DD. If
    nothing matches, returns the original text and False so the caller
    can record an Invalid Format issue.
    """
    text = str(value).strip()
    if is_empty(text):
        return "", True  # empty is a Missing Value issue, not an invalid-format one

    for pattern, order in DATE_PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        parts = match.groups()
        year, month, day = parts if order == "ymd" else (parts[2], parts[1], parts[0])
        try:
            parsed = datetime(int(year), int(month), int(day))
            return parsed.strftime("%Y-%m-%d"), True
        except ValueError:
            continue  # e.g. month=13 matched the shape but isn't a real date

    return text, False


def normalize_phone(value: Any) -> Tuple[str, bool]:
    """
    Returns (normalized_value, was_parseable). Strips everything but
    digits and a leading '+', then assumes a Saudi number: a leading 0
    becomes +966, a bare leading 966 gets a '+' added, +966... is left
    alone. Requires at least 8 digits to count as a phone number at all.
    """
    text = str(value).strip()
    if is_empty(text):
        return "", True

    digits = re.sub(r"[^\d+]", "", text)
    digit_count = sum(ch.isdigit() for ch in digits)
    if digit_count < 8:
        return text, False

    if digits.startswith("+966"):
        normalized = digits
    elif digits.startswith("966"):
        normalized = "+" + digits
    elif digits.startswith("0"):
        normalized = "+966" + digits[1:]
    else:
        normalized = "+966" + digits.lstrip("+")

    return normalized, True


def normalize_amount(value: Any) -> Tuple[Any, bool]:
    """
    Returns (normalized_value, was_parseable). Strips anything that
    isn't a digit, a dot, or a minus sign (so "SAR 1,200.00" becomes
    parseable), then converts to a float rounded to 2 decimal places.
    """
    if is_empty(value):
        return "", True
    try:
        cleaned = re.sub(r"[^\d.\-]", "", str(value))
        return round(float(cleaned), 2), True
    except ValueError:
        return value, False


def normalize_record(record: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Normalizes one record end to end. Returns (normalized_record,
    issues), where each issue dict has no record_index -- the caller
    (pipeline.py) fills that in.
    """
    issues: List[Dict[str, Any]] = []
    normalized: Dict[str, Any] = dict(record)

    normalized["record_id"] = str(record.get("record_id", "")).strip()
    normalized["full_name"] = normalize_text(record.get("full_name", ""))
    normalized["city"] = normalize_city(record.get("city", ""))
    normalized["country"] = normalize_country(record.get("country", ""))
    normalized["notes"] = normalize_text(record.get("notes", ""))

    email = record.get("email", "")
    normalized["email"] = "" if is_empty(email) else str(email).strip().lower()

    for field in ("national_id", "employee_id"):
        value = record.get(field, "")
        normalized[field] = "" if is_empty(value) else str(value).strip()

    phone_value, phone_ok = normalize_phone(record.get("phone", ""))
    normalized["phone"] = phone_value
    if not phone_ok:
        issues.append({
            "issue_type": "Invalid Format",
            "field_name": "phone",
            "description": f"'{record.get('phone')}' could not be normalized into a phone number.",
            "severity": "Warning",
        })

    date_value, date_ok = normalize_date(record.get("date_field", ""))
    normalized["date_field"] = date_value
    if not date_ok:
        issues.append({
            "issue_type": "Invalid Format",
            "field_name": "date_field",
            "description": f"'{record.get('date_field')}' is not a recognized date format.",
            "severity": "Warning",
        })

    amount_value, amount_ok = normalize_amount(record.get("amount", ""))
    normalized["amount"] = amount_value
    if not amount_ok:
        issues.append({
            "issue_type": "Invalid Format",
            "field_name": "amount",
            "description": f"'{record.get('amount')}' is not a recognized numeric amount.",
            "severity": "Warning",
        })

    return normalized, issues
