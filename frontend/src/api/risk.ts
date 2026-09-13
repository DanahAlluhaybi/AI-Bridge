// One file that knows how to talk to the risk endpoints, same pattern
// as api/systems.ts, api/adapter.ts, and api/readiness.ts.

import type { AIRiskAssessment, RiskSummary } from "../types";

const API_BASE_URL = "http://localhost:8000/api";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Request failed (HTTP ${response.status}): ${body}`);
  }
  return response.json();
}

// Runs a brand-new risk assessment (a fresh POST every time -- see the
// backend router's docstring for why this is a deliberate action, not
// something that happens automatically).
export function assessRisk(systemId: number): Promise<AIRiskAssessment> {
  return fetch(`${API_BASE_URL}/systems/${systemId}/risk-assess`, {
    method: "POST",
  }).then((r) => handle<AIRiskAssessment>(r));
}

// 404 just means "never risk-assessed yet" -- not an error worth
// showing the user, so it resolves to null instead of throwing.
export function getLatestRiskAssessment(
  systemId: number,
): Promise<AIRiskAssessment | null> {
  return fetch(`${API_BASE_URL}/systems/${systemId}/risk/latest`).then((r) =>
    r.status === 404 ? null : handle<AIRiskAssessment>(r),
  );
}

export function getRiskAssessmentHistory(
  systemId: number,
): Promise<AIRiskAssessment[]> {
  return fetch(`${API_BASE_URL}/systems/${systemId}/risk/history`).then((r) =>
    handle<AIRiskAssessment[]>(r),
  );
}

export function getRiskSummary(): Promise<RiskSummary> {
  return fetch(`${API_BASE_URL}/risk/summary`).then((r) =>
    handle<RiskSummary>(r),
  );
}
