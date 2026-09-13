"""
adapter/classify.py

Steps 4 and 5: Data Classification and Sensitive Data Detection,
implemented as one function since both start from the same question --
which sensitive-ish fields does this record actually have a value in?
Sensitive Data Detection needs that list directly; Data Classification
needs one label summarizing the whole record, derived from the same
list.

Rule:
    High-sensitivity fields:   national_id, amount (financial data)
    Medium-sensitivity fields: email, phone, employee_id

    Sensitive  if any high field has a value, or 2+ medium fields do
    Internal   if exactly 1 medium field has a value and no high field does
    Public     if no high or medium field has a value

Systems that carry financial amounts (ERP, Finance, Sales) classify as
Sensitive more often than not as a result -- that reflects the rule
deliberately erring toward over- rather than under-classifying
financial and employee data.
"""

from typing import Any, Dict, List, Tuple

from .validate import is_empty

HIGH_SENSITIVITY_FIELDS = ["national_id", "amount"]
MEDIUM_SENSITIVITY_FIELDS = ["email", "phone", "employee_id"]


def detect_sensitive_fields(record: Dict[str, Any]) -> List[str]:
    """Which of the tracked sensitive fields actually have a value in this record."""
    fields = HIGH_SENSITIVITY_FIELDS + MEDIUM_SENSITIVITY_FIELDS
    return [field for field in fields if not is_empty(record.get(field))]


def classify_record(record: Dict[str, Any]) -> Tuple[str, List[str]]:
    """Returns (classification, sensitive_fields_detected)."""
    detected = detect_sensitive_fields(record)
    high_present = any(field in detected for field in HIGH_SENSITIVITY_FIELDS)
    medium_count = sum(1 for field in detected if field in MEDIUM_SENSITIVITY_FIELDS)

    if high_present or medium_count >= 2:
        classification = "Sensitive"
    elif medium_count == 1:
        classification = "Internal"
    else:
        classification = "Public"

    return classification, detected
