// One file that knows how to talk to the AI Adoption endpoints, same
// pattern as api/readiness.ts and api/risk.ts. No "assess" call here --
// an adoption decision is always read live from a system's existing
// Readiness and Risk results.

import type { AdoptionOverview, SystemAdoption } from "../types";

const API_BASE_URL = "http://localhost:8000/api";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Request failed (HTTP ${response.status}): ${body}`);
  }
  return response.json();
}

export function getSystemAdoption(systemId: number): Promise<SystemAdoption> {
  return fetch(`${API_BASE_URL}/systems/${systemId}/adoption`).then((r) =>
    handle<SystemAdoption>(r),
  );
}

export function getAdoptionOverview(): Promise<AdoptionOverview> {
  return fetch(`${API_BASE_URL}/adoption/summary`).then((r) =>
    handle<AdoptionOverview>(r),
  );
}
