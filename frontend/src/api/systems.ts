// One file that knows how to talk to the /api/systems endpoints, so
// pages call plain functions like listSystems() instead of repeating
// fetch() + error handling everywhere they need enterprise system data.

import type { EnterpriseSystem, EnterpriseSystemInput } from "../types";

const API_BASE_URL = "http://localhost:8000/api";

export interface SystemFilters {
  status?: string;
  integration_type?: string;
  search?: string;
}

function buildQuery(filters: SystemFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.integration_type) {
    params.set("integration_type", filters.integration_type);
  }
  if (filters.search) params.set("search", filters.search);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Request failed (HTTP ${response.status}): ${body}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

// filters is optional and, by default, empty -- see the comment in
// routers/systems.py for why the frontend usually calls this with no
// filters and filters in the browser instead.
export function listSystems(
  filters: SystemFilters = {},
): Promise<EnterpriseSystem[]> {
  return fetch(`${API_BASE_URL}/systems${buildQuery(filters)}`).then((r) =>
    handle<EnterpriseSystem[]>(r),
  );
}

export function getSystem(id: number | string): Promise<EnterpriseSystem> {
  return fetch(`${API_BASE_URL}/systems/${id}`).then((r) =>
    handle<EnterpriseSystem>(r),
  );
}

export function createSystem(
  data: EnterpriseSystemInput,
): Promise<EnterpriseSystem> {
  return fetch(`${API_BASE_URL}/systems`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then((r) => handle<EnterpriseSystem>(r));
}

// Not used by any page yet (there's no Edit form), but the backend
// supports it and it's defined here so it's ready when one is added.
export function updateSystem(
  id: number,
  data: Partial<EnterpriseSystemInput>,
): Promise<EnterpriseSystem> {
  return fetch(`${API_BASE_URL}/systems/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then((r) => handle<EnterpriseSystem>(r));
}

export function deleteSystem(id: number): Promise<void> {
  return fetch(`${API_BASE_URL}/systems/${id}`, {
    method: "DELETE",
  }).then((r) => handle<void>(r));
}
