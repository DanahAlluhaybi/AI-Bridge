// Central place for the TypeScript shapes that mirror the backend's
// Pydantic schemas (backend/app/schemas.py). Keeping these in one file
// means every page/component imports the same definition of "what an
// enterprise system looks like" -- if the backend ever adds a field,
// this is the one place the frontend needs to catch up.
//
// Each union type below (e.g. SystemType) is the TypeScript equivalent
// of a Python Enum -- it restricts a field to a fixed, known list of
// values instead of "any string".

export type SystemType =
  | "ERP"
  | "HR Management"
  | "Finance"
  | "Customer Support"
  | "Sales"
  | "Other";

export type IntegrationType = "REST API" | "CSV" | "JSON" | "SQL Database";

export type DataClassification =
  | "Public"
  | "Internal"
  | "Confidential"
  | "Restricted";

export type SecurityLevel = "Low" | "Medium" | "High" | "Critical";

export type SystemStatus = "Connected" | "Disconnected" | "Pending";

export interface EnterpriseSystem {
  id: number;
  name: string;
  system_type: SystemType;
  department: string;
  owner: string;
  integration_type: IntegrationType;
  data_types: string[];
  data_classification: DataClassification;
  security_level: SecurityLevel;
  status: SystemStatus;
  data_source?: string | null;
  created_at: string;
}

// The shape used when creating/updating -- same fields, minus the ones
// only the database assigns (id, created_at).
export interface EnterpriseSystemInput {
  name: string;
  system_type: SystemType;
  department: string;
  owner: string;
  integration_type: IntegrationType;
  data_types: string[];
  data_classification: DataClassification;
  security_level: SecurityLevel;
  status: SystemStatus;
  data_source?: string;
}

export const SYSTEM_TYPES: SystemType[] = [
  "ERP",
  "HR Management",
  "Finance",
  "Customer Support",
  "Sales",
  "Other",
];

export const INTEGRATION_TYPES: IntegrationType[] = [
  "REST API",
  "CSV",
  "JSON",
  "SQL Database",
];

export const DATA_CLASSIFICATIONS: DataClassification[] = [
  "Public",
  "Internal",
  "Confidential",
  "Restricted",
];

export const SECURITY_LEVELS: SecurityLevel[] = [
  "Low",
  "Medium",
  "High",
  "Critical",
];

export const SYSTEM_STATUSES: SystemStatus[] = [
  "Connected",
  "Disconnected",
  "Pending",
];

// ---------------------------------------------------------------------------
// Legacy-to-AI Adapter
// ---------------------------------------------------------------------------
// Mirrors backend/app/schemas.py's adapter-related types the same way
// the types above mirror its enterprise-system ones.

export type SourceType = "CSV" | "JSON" | "REST API" | "SQL Database";

export type DataClassificationLevel = "Public" | "Internal" | "Sensitive";

export type IssueType =
  | "Missing Value"
  | "Invalid Format"
  | "Duplicate Record"
  | "Sensitive Field";

export type IssueSeverity = "Info" | "Warning";

export const SOURCE_TYPES: SourceType[] = [
  "CSV",
  "JSON",
  "REST API",
  "SQL Database",
];

// One AdapterSource = one enterprise system's mock raw data feed,
// seeded in backend/app/seed_data.py (one per enterprise system).
export interface AdapterSource {
  id: number;
  system_id: number;
  system_name: string;
  source_type: SourceType;
  description?: string | null;
}

// A single record's before/after -- this is what fills the "Before /
// After" table on the Data Adapter page. raw_data/normalized_data are
// intentionally untyped objects: the fields differ per source (a
// vendor record and an employee record don't share a shape), so the
// frontend just renders whichever keys are present.
export interface ProcessingResult {
  id: number;
  record_index: number;
  raw_data: Record<string, unknown>;
  normalized_data: Record<string, unknown>;
  classification: DataClassificationLevel;
  is_duplicate: boolean;
  sensitive_fields: string[];
}

export interface DetectedIssue {
  id: number;
  record_index: number | null;
  issue_type: IssueType;
  field_name?: string | null;
  description: string;
  severity: IssueSeverity;
}

// ---------------------------------------------------------------------------
// AI Readiness Assessment
// ---------------------------------------------------------------------------

export type ReadinessLevel =
  | "AI Ready"
  | "Mostly Ready"
  | "Needs Improvement"
  | "Not Ready";

// Fixed order the dimensions are always shown in, matching
// backend/app/readiness/engine.py's WEIGHTS dict.
export const DIMENSION_ORDER: string[] = [
  "Data Quality",
  "Data Availability",
  "Data Integration",
  "Technical Readiness",
  "Security",
  "Privacy",
  "Governance",
  "Human Oversight",
];

export interface DimensionGap {
  dimension: string;
  score: number;
  description: string;
}

export interface AIReadinessAssessment {
  id: number;
  system_id: number;
  system_name: string;
  overall_score: number;
  readiness_level: ReadinessLevel;
  dimension_scores: Record<string, number>;
  identified_gaps: DimensionGap[];
  recommendations: string[];
  created_at: string;
}

export interface SystemGovernanceGap {
  system_id: number;
  system_name: string;
  score: number;
  description: string;
}

// What GET /api/readiness/summary returns -- the Dashboard's readiness
// numbers, always computed live from actual assessments.
export interface ReadinessSummary {
  systems_total: number;
  systems_assessed: number;
  average_score: number | null;
  ai_ready_count: number;
  mostly_ready_count: number;
  needs_improvement_count: number;
  not_ready_count: number;
  top_governance_gaps: SystemGovernanceGap[];
}

// ---------------------------------------------------------------------------
// AI Risk Engine
// ---------------------------------------------------------------------------

export type RiskLevel = "Low" | "Medium" | "High" | "Critical";

// Fixed order the risk factors are always shown in, matching
// backend/app/risk/engine.py's WEIGHTS dict.
export const RISK_FACTOR_ORDER: string[] = [
  "Data Sensitivity",
  "Security Gap",
  "Readiness Gap",
  "Oversight Gap",
];

export interface RiskDriver {
  factor: string;
  score: number;
  description: string;
}

export interface AIRiskAssessment {
  id: number;
  system_id: number;
  system_name: string;
  risk_score: number;
  risk_level: RiskLevel;
  risk_factors: Record<string, number>;
  risk_drivers: RiskDriver[];
  created_at: string;
}

export interface SystemRiskFlag {
  system_id: number;
  system_name: string;
  risk_score: number;
  risk_level: RiskLevel;
}

// What GET /api/risk/summary returns -- the Dashboard's risk numbers,
// always computed live from actual assessments.
export interface RiskSummary {
  systems_total: number;
  systems_assessed: number;
  average_risk_score: number | null;
  low_count: number;
  medium_count: number;
  high_count: number;
  critical_count: number;
  highest_risk_systems: SystemRiskFlag[];
}

// ---------------------------------------------------------------------------
// AI Adoption & Automation Opportunities
// ---------------------------------------------------------------------------
// No history here, unlike Readiness/Risk -- an AI Adoption decision is
// always a live read of a system's latest Readiness + Risk results
// (see backend/app/adoption/engine.py), not a separate saved run.

export type AdoptionDecision =
  | "Good Candidate"
  | "Conditional"
  | "Not Yet"
  | "Not Recommended"
  | "Insufficient Information";

export type AutomationPotential = "Low" | "Medium" | "High";
export type BusinessImpact = "Low" | "Medium" | "High";
export type AutomationRisk = "Low" | "Medium" | "High";
export type HumanOversight = "Required" | "Recommended" | "Not required";

export interface AutomationOpportunity {
  id: number;
  system_id: number;
  activity: string;
  description: string;
  ai_opportunity: string;
  automation_potential: AutomationPotential | null;
  business_impact: BusinessImpact | null;
  automation_risk: AutomationRisk | null;
  human_oversight: HumanOversight | null;
  priority_score: number | null;
  recommendation: string;
}

export interface SystemAdoption {
  system_id: number;
  system_name: string;
  readiness_score: number | null;
  risk_level: RiskLevel | null;
  decision: AdoptionDecision;
  reason: string;
  opportunities: AutomationOpportunity[];
}

export interface AdoptionOverviewRow {
  system_id: number;
  system_name: string;
  readiness_score: number | null;
  risk_level: RiskLevel | null;
  decision: AdoptionDecision;
  top_opportunity: string | null;
}

export interface AdoptionOverview {
  systems: AdoptionOverviewRow[];
}

// ---------------------------------------------------------------------------
// AI Use Cases, Human Approval, AI Passport, AI Playground, Audit Log
// ---------------------------------------------------------------------------
// Mirrors backend/app/schemas.py's governance-layer types. AI Adoption
// (above) answers "should this system use AI at all" -- these answer
// the narrower question, per proposed use, of "should this specific
// use go ahead, and does a human need to sign off first".

export type AutomationLevel = "Advisory" | "Assisted" | "Full";
export type UseCaseStatus = "Proposed" | "Approved" | "Rejected";
export type PolicyDecision = "ALLOW" | "HUMAN_APPROVAL" | "BLOCK";

export const AUTOMATION_LEVELS: AutomationLevel[] = ["Advisory", "Assisted", "Full"];

export interface AIUseCase {
  id: number;
  system_id: number;
  system_name: string;
  name: string;
  purpose: string;
  owner: string;
  requested_automation_level: AutomationLevel;
  policy_decision: PolicyDecision;
  policy_reason: string;
  status: UseCaseStatus;
  created_at: string;
}

// What the client sends on POST /api/use-cases -- system_id plus the
// fields the person proposing the use case actually chooses.
export interface AIUseCaseInput {
  system_id: number;
  name: string;
  purpose: string;
  owner: string;
  requested_automation_level: AutomationLevel;
}

export interface ApprovalRequest {
  id: number;
  use_case_id: number;
  use_case_name: string;
  system_name: string;
  status: string;
  reason: string;
  decided_by?: string | null;
  decision_notes?: string | null;
  created_at: string;
  decided_at?: string | null;
}

// What the client sends on POST /api/approvals/{id}/decide.
export interface ApprovalDecisionInput {
  approve: boolean;
  decided_by: string;
  notes?: string;
}

// A read-only summary document for one use case -- everything an
// approver or auditor would need on one screen. Reflects the decision
// actually recorded at proposal time, not a live re-assessment.
export interface AIPassport {
  use_case_id: number;
  use_case_name: string;
  purpose: string;
  owner: string;
  system_id: number;
  system_name: string;
  data_classification: DataClassification;
  security_level: SecurityLevel;
  readiness_score: number | null;
  risk_level: RiskLevel | null;
  adoption_decision: AdoptionDecision;
  requested_automation_level: AutomationLevel;
  policy_decision: PolicyDecision;
  policy_reason: string;
  use_case_status: UseCaseStatus;
  use_case_created_at: string;
  generated_at: string;
}

export interface PlaygroundRequestInput {
  use_case_id: number;
  prompt: string;
}

export interface PlaygroundRequest {
  id: number;
  use_case_id: number;
  use_case_name: string;
  prompt: string;
  response: string;
  created_at: string;
}

export interface AuditLogEntry {
  id: number;
  action: string;
  summary: string;
  entity_type?: string | null;
  entity_id?: number | null;
  created_at: string;
}

// The summary returned right after POST /adapter/sources/{id}/process,
// and also what GET /adapter/jobs lists (one row per past run).
export interface ProcessingJob {
  id: number;
  source_id: number;
  status: string;
  started_at: string;
  completed_at?: string | null;
  records_processed: number;
  records_cleaned: number;
  duplicate_records: number;
  issues_detected: number;
  sensitive_fields_detected: number;
  classification_summary: Record<string, number>;
  // Deliberately not the full AI Readiness Score (see readiness/engine.py) --
  // just a pass/fail read on unresolved data-quality issues.
  ai_readiness_status: string;
}

// What the Data Adapter page actually renders: the job summary plus
// every record's before/after and every issue found.
export interface ProcessingJobDetail extends ProcessingJob {
  results: ProcessingResult[];
  issues: DetectedIssue[];
}
