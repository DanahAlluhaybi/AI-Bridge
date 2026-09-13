"""
schemas.py

Pydantic request/response schemas -- the API contract. models.py
describes what a row looks like in SQLite; this file describes what
JSON a client may send and what JSON the API promises to return.

Separating the two matters in a few concrete ways: a database row has
fields (id, created_at) a client should never set directly; an update
request should be able to send only the fields it's changing rather
than the whole object; and Pydantic validates incoming data before it
reaches any database code, rejecting an invalid value with a clear 422
instead of a downstream error.

The Enums below define the controlled vocabulary for each field --
locking values like data_classification down to a fixed list is what
lets later logic (scoring, dashboards) reliably group and count systems
without dealing with free-text variants of the same value.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SystemType(str, Enum):
    ERP = "ERP"
    HR = "HR Management"
    FINANCE = "Finance"
    CUSTOMER_SUPPORT = "Customer Support"
    SALES = "Sales"
    OTHER = "Other"


class IntegrationType(str, Enum):
    REST_API = "REST API"
    CSV = "CSV"
    JSON = "JSON"
    SQL_DATABASE = "SQL Database"


class DataClassification(str, Enum):
    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    RESTRICTED = "Restricted"


class SecurityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class SystemStatus(str, Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    PENDING = "Pending"


class EnterpriseSystemBase(BaseModel):
    """Fields every enterprise system has, shared by Create and Out."""

    name: str = Field(min_length=2, max_length=120)
    system_type: SystemType
    department: str = Field(min_length=2, max_length=120)
    owner: str = Field(min_length=2, max_length=160)
    integration_type: IntegrationType
    data_types: List[str] = Field(default_factory=list)
    data_classification: DataClassification
    security_level: SecurityLevel
    status: SystemStatus = SystemStatus.PENDING
    data_source: Optional[str] = None


class EnterpriseSystemCreate(EnterpriseSystemBase):
    """What the client sends on POST /api/systems."""


class EnterpriseSystemUpdate(BaseModel):
    """
    What the client sends on PUT /api/systems/{id}. Every field is
    optional so a partial update (e.g. just `status`) doesn't require
    resending the whole record -- the router only applies fields that
    were actually sent (`exclude_unset=True`).
    """

    name: Optional[str] = None
    system_type: Optional[SystemType] = None
    department: Optional[str] = None
    owner: Optional[str] = None
    integration_type: Optional[IntegrationType] = None
    data_types: Optional[List[str]] = None
    data_classification: Optional[DataClassification] = None
    security_level: Optional[SecurityLevel] = None
    status: Optional[SystemStatus] = None
    data_source: Optional[str] = None


class EnterpriseSystemOut(EnterpriseSystemBase):
    """What the API returns. Adds the fields the database owns."""

    id: int
    created_at: datetime

    # Allows building this schema directly from a SQLAlchemy model
    # instance (system.name, system.id, ...) rather than only a dict.
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Legacy-to-AI Adapter
# ---------------------------------------------------------------------------
# No "Create" schema for these -- sources come from seed_data.py, and
# jobs/results/issues are only ever produced by running the adapter
# (adapter/pipeline.py), so every schema below is an output shape.


class SourceType(str, Enum):
    CSV = "CSV"
    JSON = "JSON"
    REST_API = "REST API"
    SQL_DATABASE = "SQL Database"


class DataClassificationLevel(str, Enum):
    PUBLIC = "Public"
    INTERNAL = "Internal"
    SENSITIVE = "Sensitive"


class IssueType(str, Enum):
    MISSING_VALUE = "Missing Value"
    INVALID_FORMAT = "Invalid Format"
    DUPLICATE_RECORD = "Duplicate Record"
    SENSITIVE_FIELD = "Sensitive Field"


class IssueSeverity(str, Enum):
    INFO = "Info"
    WARNING = "Warning"


class AdapterSourceOut(BaseModel):
    id: int
    system_id: int
    # Not a column on AdapterSource -- the router looks up the linked
    # EnterpriseSystem and fills this in.
    system_name: str
    source_type: SourceType
    description: Optional[str] = None


class ProcessingResultOut(BaseModel):
    id: int
    record_index: int
    raw_data: Dict[str, Any]
    normalized_data: Dict[str, Any]
    classification: DataClassificationLevel
    is_duplicate: bool
    sensitive_fields: List[str]

    model_config = ConfigDict(from_attributes=True)


class DetectedIssueOut(BaseModel):
    id: int
    record_index: Optional[int]
    issue_type: IssueType
    field_name: Optional[str]
    description: str
    severity: IssueSeverity

    model_config = ConfigDict(from_attributes=True)


class ProcessingJobOut(BaseModel):
    id: int
    source_id: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    records_processed: int
    records_cleaned: int
    duplicate_records: int
    issues_detected: int
    sensitive_fields_detected: int
    classification_summary: Dict[str, int]
    ai_readiness_status: str

    model_config = ConfigDict(from_attributes=True)


class ProcessingJobDetail(ProcessingJobOut):
    """A job plus everything it produced -- returned by /process and /jobs/{id}."""

    results: List[ProcessingResultOut]
    issues: List[DetectedIssueOut]


# ---------------------------------------------------------------------------
# AI Readiness Assessment
# ---------------------------------------------------------------------------
# No "Create" schema here either -- an assessment is only ever produced
# by POSTing to /systems/{id}/assess, which runs
# readiness/engine.py's run_assessment() and returns the result.


class ReadinessLevel(str, Enum):
    AI_READY = "AI Ready"
    MOSTLY_READY = "Mostly Ready"
    NEEDS_IMPROVEMENT = "Needs Improvement"
    NOT_READY = "Not Ready"


class DimensionGap(BaseModel):
    """One weak dimension, with the score that triggered it and a plain-language explanation."""

    dimension: str
    score: int
    description: str


class AIReadinessAssessmentOut(BaseModel):
    id: int
    system_id: int
    # Not a column on the model -- filled in by the router from the
    # linked EnterpriseSystem.
    system_name: str
    overall_score: int = Field(ge=0, le=100)
    readiness_level: ReadinessLevel
    dimension_scores: Dict[str, int]
    identified_gaps: List[DimensionGap]
    recommendations: List[str]
    created_at: datetime


class SystemGovernanceGap(BaseModel):
    """One system's Governance gap, for the dashboard's 'top governance gaps' list."""

    system_id: int
    system_name: str
    score: int
    description: str


class ReadinessSummary(BaseModel):
    """
    Backs the dashboard's readiness overview. Built from each system's
    most recent assessment only -- a system assessed three times still
    counts once, using its latest result.
    """

    systems_total: int
    systems_assessed: int
    average_score: Optional[float] = None
    ai_ready_count: int
    mostly_ready_count: int
    needs_improvement_count: int
    not_ready_count: int
    top_governance_gaps: List[SystemGovernanceGap]


# ---------------------------------------------------------------------------
# AI Risk Engine
# ---------------------------------------------------------------------------
# No "Create" schema here either -- a risk assessment is only ever
# produced by POSTing to /systems/{id}/risk-assess, which runs
# risk/engine.py's run_risk_assessment() and returns the result.


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RiskDriver(BaseModel):
    """One risk factor that scored high enough to call out specifically."""

    factor: str
    score: int
    description: str


class AIRiskAssessmentOut(BaseModel):
    id: int
    system_id: int
    # Not a column on the model -- filled in by the router from the
    # linked EnterpriseSystem.
    system_name: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    risk_factors: Dict[str, int]
    risk_drivers: List[RiskDriver]
    created_at: datetime


class SystemRiskFlag(BaseModel):
    """One system's risk assessment, for the dashboard's 'highest risk systems' list."""

    system_id: int
    system_name: str
    risk_score: int
    risk_level: RiskLevel


class RiskSummary(BaseModel):
    """
    Backs the dashboard's risk overview. Built from each system's most
    recent risk assessment only -- a system assessed three times still
    counts once, using its latest result.
    """

    systems_total: int
    systems_assessed: int
    average_risk_score: Optional[float] = None
    low_count: int
    medium_count: int
    high_count: int
    critical_count: int
    highest_risk_systems: List[SystemRiskFlag]


# ---------------------------------------------------------------------------
# AI Adoption & Automation Opportunities
# ---------------------------------------------------------------------------
# No "Create"/history schemas here -- an AI Adoption decision is a live
# read of a system's most recent Readiness + Risk assessments (see
# adoption/engine.py), not something a user separately runs and saves.


class AdoptionDecision(str, Enum):
    GOOD_CANDIDATE = "Good Candidate"
    CONDITIONAL = "Conditional"
    NOT_YET = "Not Yet"
    NOT_RECOMMENDED = "Not Recommended"
    INSUFFICIENT_INFORMATION = "Insufficient Information"


class AutomationPotential(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class BusinessImpact(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class AutomationRisk(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class HumanOversight(str, Enum):
    REQUIRED = "Required"
    RECOMMENDED = "Recommended"
    NOT_REQUIRED = "Not required"


class AutomationOpportunityOut(BaseModel):
    """
    One employee activity plus what AI Bridge thinks should happen to
    it. The four Optional fields are null only when the underlying
    activity record is missing required information -- Bridge would
    rather say so than guess (see opportunities.is_activity_complete).
    """

    id: int
    system_id: int
    activity: str
    description: str
    ai_opportunity: str
    automation_potential: Optional[AutomationPotential]
    business_impact: Optional[BusinessImpact]
    automation_risk: Optional[AutomationRisk]
    human_oversight: Optional[HumanOversight]
    priority_score: Optional[int]
    recommendation: str


class SystemAdoptionOut(BaseModel):
    """What GET /api/systems/{id}/adoption returns."""

    system_id: int
    system_name: str
    readiness_score: Optional[int]
    risk_level: Optional[RiskLevel]
    decision: AdoptionDecision
    reason: str
    opportunities: List[AutomationOpportunityOut]


class AdoptionOverviewRow(BaseModel):
    """One system's row on the AI Adoption Overview page."""

    system_id: int
    system_name: str
    readiness_score: Optional[int]
    risk_level: Optional[RiskLevel]
    decision: AdoptionDecision
    top_opportunity: Optional[str] = None


class AdoptionOverview(BaseModel):
    systems: List[AdoptionOverviewRow]


# ---------------------------------------------------------------------------
# AI Use Cases, Human Approval, AI Passport, AI Playground, Audit Log
# ---------------------------------------------------------------------------


class AutomationLevel(str, Enum):
    ADVISORY = "Advisory"
    ASSISTED = "Assisted"
    FULL = "Full"


class UseCaseStatus(str, Enum):
    PROPOSED = "Proposed"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    BLOCK = "BLOCK"


class AIUseCaseCreate(BaseModel):
    system_id: int
    name: str = Field(min_length=2, max_length=160)
    purpose: str = Field(min_length=2, max_length=500)
    owner: str = Field(min_length=2, max_length=160)
    requested_automation_level: AutomationLevel = AutomationLevel.ASSISTED


class AIUseCaseOut(BaseModel):
    id: int
    system_id: int
    system_name: str
    name: str
    purpose: str
    owner: str
    requested_automation_level: AutomationLevel
    policy_decision: PolicyDecision
    policy_reason: str
    status: UseCaseStatus
    created_at: datetime


class ApprovalRequestOut(BaseModel):
    id: int
    use_case_id: int
    use_case_name: str
    system_name: str
    status: str
    reason: str
    decided_by: Optional[str] = None
    decision_notes: Optional[str] = None
    created_at: datetime
    decided_at: Optional[datetime] = None


class ApprovalDecision(BaseModel):
    """What the client sends to POST /approvals/{id}/decide."""

    approve: bool
    decided_by: str = Field(min_length=1, max_length=160)
    notes: Optional[str] = None


class AIPassportOut(BaseModel):
    """
    A read-only summary document for one use case -- everything an
    approver or auditor would need on one screen: what's being
    proposed, the system it touches, and the Readiness/Risk/Adoption
    picture behind the decision that was actually recorded for it.
    """

    use_case_id: int
    use_case_name: str
    purpose: str
    owner: str
    system_id: int
    system_name: str
    data_classification: DataClassification
    security_level: SecurityLevel
    readiness_score: Optional[int]
    risk_level: Optional[RiskLevel]
    adoption_decision: AdoptionDecision
    requested_automation_level: AutomationLevel
    policy_decision: PolicyDecision
    policy_reason: str
    use_case_status: UseCaseStatus
    use_case_created_at: datetime
    generated_at: datetime


class PlaygroundRequestCreate(BaseModel):
    use_case_id: int
    prompt: str = Field(min_length=1, max_length=2000)


class PlaygroundRequestOut(BaseModel):
    id: int
    use_case_id: int
    use_case_name: str
    prompt: str
    response: str
    created_at: datetime


class AuditLogEntryOut(BaseModel):
    id: int
    action: str
    summary: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    created_at: datetime
