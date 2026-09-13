"""
models.py

SQLAlchemy table definitions. Each class here is one table in
ai_bridge.db.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String

from .database import Base


class HealthPing(Base):
    __tablename__ = "health_pings"

    id = Column(Integer, primary_key=True, index=True)
    checked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    source = Column(String, default="unknown")


class EnterpriseSystem(Base):
    """
    One row = one enterprise system AI Bridge knows about (ERP, HR,
    Finance, etc.). Everything downstream -- the adapter pipeline, the
    readiness engine -- operates on one of these.

    Classification/status/etc. are stored as plain strings rather than
    a SQL ENUM type; the allowed values are enforced at the API layer
    (schemas.py) instead, which is easier to change later.
    """

    __tablename__ = "enterprise_systems"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    system_type = Column(String, nullable=False)
    department = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    integration_type = Column(String, nullable=False)
    data_types = Column(JSON, nullable=False, default=list)
    data_classification = Column(String, nullable=False)
    security_level = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Pending")
    data_source = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AdapterSource(Base):
    """
    One row = one mock data feed the Legacy-to-AI Adapter can pull
    from. Tied to exactly one EnterpriseSystem (`unique=True` on
    system_id). `sample_file` names a file under
    mock-data/adapter_sources/ -- see adapter/extract.py for how
    source_type picks the extraction function that reads it.
    """

    __tablename__ = "adapter_sources"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("enterprise_systems.id"), nullable=False, unique=True)
    source_type = Column(String, nullable=False)  # CSV / JSON / REST API / SQL Database
    sample_file = Column(String, nullable=False)
    description = Column(String, nullable=True)


class ProcessingJob(Base):
    """
    One row = one run of the adapter against one AdapterSource. Holds
    the summary of that run; per-record detail lives in
    ProcessingResult and DetectedIssue, linked back here by job_id.
    """

    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("adapter_sources.id"), nullable=False)
    status = Column(String, nullable=False, default="Completed")
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    records_processed = Column(Integer, default=0)
    records_cleaned = Column(Integer, default=0)
    duplicate_records = Column(Integer, default=0)
    issues_detected = Column(Integer, default=0)
    sensitive_fields_detected = Column(Integer, default=0)
    classification_summary = Column(JSON, default=dict)  # {"Public": 2, "Internal": 1, "Sensitive": 3}
    # A basic pass/fail read on unresolved quality issues -- not the AI
    # Readiness Score, which is a separately calculated value (see
    # readiness/engine.py).
    ai_readiness_status = Column(String, nullable=False, default="Needs Attention")


class ProcessingResult(Base):
    """
    One row = one record from a source, before and after the adapter
    touched it. raw_data/normalized_data hold the full record as JSON.
    """

    __tablename__ = "processing_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("processing_jobs.id"), nullable=False)
    record_index = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=False)
    normalized_data = Column(JSON, nullable=False)
    classification = Column(String, nullable=False)  # Public / Internal / Sensitive
    is_duplicate = Column(Boolean, default=False)
    sensitive_fields = Column(JSON, default=list)  # e.g. ["email", "national_id"]


class DetectedIssue(Base):
    """
    One row = one thing the adapter noticed about the data -- a
    missing value, an unparseable format, a duplicate record, or a
    field flagged as sensitive. record_index is null for a job-level
    issue (none exist yet, but the column allows one without a schema
    change).
    """

    __tablename__ = "detected_issues"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("processing_jobs.id"), nullable=False)
    record_index = Column(Integer, nullable=True)
    issue_type = Column(String, nullable=False)
    field_name = Column(String, nullable=True)
    description = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="Warning")  # Info / Warning


class AIReadinessAssessment(Base):
    """
    One row = one run of the AI Readiness Assessment engine against
    one EnterpriseSystem. A history table, not one row per system --
    a system can be assessed more than once, and the router always
    treats the newest row as the current assessment while older ones
    stay queryable.
    """

    __tablename__ = "ai_readiness_assessments"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("enterprise_systems.id"), nullable=False)
    overall_score = Column(Integer, nullable=False)
    readiness_level = Column(String, nullable=False)
    dimension_scores = Column(JSON, nullable=False)  # {"Data Quality": 67, ...}
    identified_gaps = Column(JSON, default=list)  # [{"dimension":..., "score":..., "description":...}]
    recommendations = Column(JSON, default=list)  # [str, ...]
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SystemActivity(Base):
    """
    One row = one repetitive employee activity recorded against an
    EnterpriseSystem -- the raw material the AI Adoption engine turns
    into an Automation Opportunity (see adoption/opportunities.py).

    Unlike AdapterSource, a system can have several of these. The six
    Low/Medium/High fields below are exactly what
    adoption/opportunities.py reads to score one activity, so this
    model's shape and that module's REQUIRED_FIELDS have to stay in
    sync by hand -- there's no foreign-key-style link enforcing it.
    """

    __tablename__ = "system_activities"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("enterprise_systems.id"), nullable=False)
    activity = Column(String, nullable=False)
    description = Column(String, nullable=False)
    ai_opportunity = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    volume = Column(String, nullable=False)
    manual_effort = Column(String, nullable=False)
    human_judgment = Column(String, nullable=False)
    data_sensitivity = Column(String, nullable=False)
    process_standardization = Column(String, nullable=False)


class AIUseCase(Base):
    """
    One proposed use of AI against one enterprise system -- Phase 7.
    `policy_decision` and `policy_reason` are computed once, at
    creation, by use_cases/policy.py (from the system's Readiness +
    Risk + AI Adoption decision at that moment) and stored here rather
    than recomputed live -- a use case's recorded decision is meant to
    stay a stable snapshot even if the system is re-assessed later,
    the same way an AI Passport should reflect what was actually
    decided, not silently drift.
    """

    __tablename__ = "ai_use_cases"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("enterprise_systems.id"), nullable=False)
    name = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    requested_automation_level = Column(String, nullable=False, default="Assisted")
    policy_decision = Column(String, nullable=False)
    policy_reason = Column(String, nullable=False)
    status = Column(String, nullable=False, default="Proposed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ApprovalRequest(Base):
    """
    One row = one pending-or-decided human approval, created
    automatically when a use case's policy decision comes back
    HUMAN_APPROVAL (see routers/use_cases.py). Deciding one updates
    the linked AIUseCase.status to match.
    """

    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    use_case_id = Column(Integer, ForeignKey("ai_use_cases.id"), nullable=False)
    status = Column(String, nullable=False, default="Pending")
    reason = Column(String, nullable=False)
    decided_by = Column(String, nullable=True)
    decision_notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    decided_at = Column(DateTime, nullable=True)


class PlaygroundRequest(Base):
    """
    One row = one prompt sent through the AI Playground for an
    Approved use case, and the MockAIProvider response it got back.
    Kept as history so a use case's playground activity can be
    reviewed later, the same reasoning as every other history table
    in this app.
    """

    __tablename__ = "playground_requests"

    id = Column(Integer, primary_key=True, index=True)
    use_case_id = Column(Integer, ForeignKey("ai_use_cases.id"), nullable=False)
    prompt = Column(String, nullable=False)
    response = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLogEntry(Base):
    """
    One row = one recorded action anywhere in AI Bridge worth keeping
    a trail of -- a system created or removed, an assessment run, a
    use case proposed, an approval decided, a playground request made.
    Written through the single helper in audit.py rather than each
    router constructing rows by hand.
    """

    __tablename__ = "audit_log_entries"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AIRiskAssessment(Base):
    """
    One row = one run of the AI Risk Engine against one
    EnterpriseSystem. Same history-table shape as
    AIReadinessAssessment -- a system can be risk-assessed more than
    once, and the newest row is always the current one.
    """

    __tablename__ = "ai_risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    system_id = Column(Integer, ForeignKey("enterprise_systems.id"), nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)
    risk_factors = Column(JSON, nullable=False)  # {"Data Sensitivity": 60, ...}
    risk_drivers = Column(JSON, default=list)  # [{"factor":..., "score":..., "description":...}]
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
