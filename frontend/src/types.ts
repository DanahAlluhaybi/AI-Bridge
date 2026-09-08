// Central place for the TypeScript shapes that mirror the backend's
// Pydantic schemas (backend/app/schemas.py). Keeping these in one file
// means every page/component imports the SAME definition of "what an
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
