// One file that knows how to talk to the readiness endpoints, same
// pattern as api/systems.ts and api/adapter.ts.

import type { AIReadinessAssessment, ReadinessSummary } from "../types";

const API_BASE_URL = "http://localhost:8000/api";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Request failed (HTTP ${response.status}): ${body}`);
  }
  return response.json();
}

// Runs a brand-new assessment (a fresh POST every time -- see the
// backend router's docstring for why this is a deliberate action, not
// something that happens automatically).
export function assessSystem(systemId: number): Promise<AIReadinessAssessment> {
  return fetch(`${API_BASE_URL}/systems/${systemId}/assess`, {
    method: "POST",
  }).then((r) => handle<AIReadinessAssessment>(r));
}

// 404 just means "never assessed yet" -- not an error worth showing
// the user, so it resolves to null instead of throwing.
export function getLatestAssessment(
  systemId: number,
): Promise<AIReadinessAssessment | null> {
  return fetch(`${API_BASE_URL}/systems/${systemId}/readiness/latest`).then(
    (r) => (r.status === 404 ? null : handle<AIReadinessAssessment>(r)),
  );
}

export function getAssessmentHistory(
  systemId: number,
): Promise<AIReadinessAssessment[]> {
  return fetch(`${API_BASE_URL}/systems/${systemId}/readiness/history`).then(
    (r) => handle<AIReadinessAssessment[]>(r),
  );
}

export function getReadinessSummary(): Promise<ReadinessSummary> {
  return fetch(`${API_BASE_URL}/readiness/summary`).then((r) =>
    handle<ReadinessSummary>(r),
  );
}
