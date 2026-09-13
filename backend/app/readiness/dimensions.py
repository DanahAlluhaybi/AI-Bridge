"""
readiness/dimensions.py

Turns what's known about a system (its Enterprise Systems profile, and
its latest Legacy-to-AI Adapter run, if any) into eight 0-100 scores,
one per readiness dimension.

Every function here is pure: same inputs, same output, every time --
no AI model call, nothing random. None of them touch the database or
FastAPI; they take plain values in and return a plain int out, which
also makes them straightforward to test in isolation.
"""


def _clamp(score: float) -> int:
    """Every dimension score is 0-100, always a whole number."""
    return max(0, min(100, round(score)))


# ---------------------------------------------------------------------------
# 1. Data Quality -- 15%
# ---------------------------------------------------------------------------
def score_data_quality(has_adapter_run: bool, issues_detected: int, records_processed: int) -> int:
    """
    How much of this system's data, on its last adapter run, still had
    a quality problem: a missing value, an invalid format, or a
    duplicate record. (issues_detected excludes sensitive-field flags
    -- see adapter/pipeline.py -- so this is a pure quality signal.)

    No adapter run yet -> neutral 50. Otherwise: start at 100 and
    subtract a point per percent of records that had an issue.
    """
    if not has_adapter_run or records_processed == 0:
        return 50
    issue_rate = issues_detected / records_processed
    return _clamp(100 - issue_rate * 100)


# ---------------------------------------------------------------------------
# 2. Data Availability -- 10%
# ---------------------------------------------------------------------------
_STATUS_POINTS = {"Connected": 40, "Pending": 20, "Disconnected": 0}


def score_data_availability(status: str, has_data_source: bool, has_adapter_source: bool) -> int:
    """
    Can this system's data actually be reached right now? Connection
    status (40/20/0), a configured data source (+30), and whether an
    adapter source exists for it at all (+30).
    """
    score = _STATUS_POINTS.get(status, 0)
    if has_data_source:
        score += 30
    if has_adapter_source:
        score += 30
    return _clamp(score)


# ---------------------------------------------------------------------------
# 3. Data Integration -- 15%
# ---------------------------------------------------------------------------
_INTEGRATION_POINTS = {
    "REST API": 100,
    "SQL Database": 90,
    "JSON": 75,
    "CSV": 55,
}


def score_data_integration(integration_type: str) -> int:
    """
    How readily the system's data can be pulled on demand. A live REST
    API or queryable SQL database scores highest; a JSON export is
    structured but usually a batch snapshot; CSV is the least ready --
    manual, easy to malform, no query capability.
    """
    return _clamp(_INTEGRATION_POINTS.get(integration_type, 50))


# ---------------------------------------------------------------------------
# 4. Technical Readiness -- 15%
# ---------------------------------------------------------------------------
def score_technical_readiness(has_adapter_run: bool, integration_type: str, status: str) -> int:
    """
    Whether the pipeline has actually been proven end to end, not just
    whether it could work in theory (that's Data Integration): has the
    adapter run against this system's data (+40), does it expose
    something queryable rather than only file exports (+30 vs +15), is
    it currently connected (+30).
    """
    score = 40 if has_adapter_run else 0
    score += 30 if integration_type in ("REST API", "SQL Database") else 15
    score += {"Connected": 30, "Pending": 15, "Disconnected": 0}.get(status, 0)
    return _clamp(score)


# ---------------------------------------------------------------------------
# 5. Security -- 15%
# ---------------------------------------------------------------------------
_SECURITY_POINTS = {"Low": 40, "Medium": 65, "High": 85, "Critical": 100}


def score_security(security_level: str) -> int:
    """Maps the system's declared security level to a readiness score directly."""
    return _clamp(_SECURITY_POINTS.get(security_level, 50))


# ---------------------------------------------------------------------------
# 6. Privacy -- 10%
# ---------------------------------------------------------------------------
_PRIVACY_CLASSIFICATION_PENALTY = {"Public": 0, "Internal": 10, "Confidential": 20, "Restricted": 30}


def score_privacy(has_adapter_run: bool, sensitive_ratio: float, data_classification: str) -> int:
    """
    Two signals, both reducing the score: the proportion of records
    the last adapter run found to be Sensitive, and the system's own
    declared data_classification. More real exposure and a higher
    declared classification both mean more privacy controls are needed.
    """
    if not has_adapter_run:
        return 50
    penalty = sensitive_ratio * 70 + _PRIVACY_CLASSIFICATION_PENALTY.get(data_classification, 15)
    return _clamp(100 - penalty)


# ---------------------------------------------------------------------------
# 7. Governance -- 10%
# ---------------------------------------------------------------------------
_GOVERNANCE_CLASSIFICATION_PENALTY = {"Public": 0, "Internal": 5, "Confidential": 15, "Restricted": 25}


def score_governance(status: str, data_classification: str) -> int:
    """
    No formal governance policy or audit trail exists yet, so this is
    a proxy: every system already has a named owner and department, so
    every system starts from a base score reflecting that. A connected,
    monitored system adds a little more; a higher data classification
    subtracts more, since more sensitive data needs stronger governance
    controls than currently exist.
    """
    score = 60
    if status == "Connected":
        score += 20
    score -= _GOVERNANCE_CLASSIFICATION_PENALTY.get(data_classification, 10)
    return _clamp(score)


# ---------------------------------------------------------------------------
# 8. Human Oversight -- 10%
# ---------------------------------------------------------------------------
_OVERSIGHT_CLASSIFICATION_PENALTY = {"Public": 0, "Internal": 10, "Confidential": 25, "Restricted": 40}


def score_human_oversight(data_classification: str) -> int:
    """
    No approval workflow exists yet, so this measures the size of the
    gap rather than real oversight activity: the more sensitive a
    system's data, the more human review it will eventually need, and
    the larger the deduction reflects that no such process exists yet.
    """
    return _clamp(100 - _OVERSIGHT_CLASSIFICATION_PENALTY.get(data_classification, 15))
