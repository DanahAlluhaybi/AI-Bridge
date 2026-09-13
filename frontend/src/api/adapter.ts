// One file that knows how to talk to the /api/adapter endpoints, so
// the Data Adapter page calls plain functions instead of repeating
// fetch()/error-handling itself.

import type { AdapterSource, ProcessingJobDetail } from "../types";

const API_BASE_URL = "http://localhost:8000/api";

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

export function listAdapterSources(): Promise<AdapterSource[]> {
  return fetch(`${API_BASE_URL}/adapter/sources`).then((r) =>
    handle<AdapterSource[]>(r),
  );
}

// Runs the whole Extraction -> Validation -> Normalization ->
// Classification -> Sensitive Data Detection pipeline for one source
// and returns the full result in one response -- no separate "check
// status" step, since this finishes instantly against a small mock
// dataset rather than a real external system.
export function processSource(sourceId: number): Promise<ProcessingJobDetail> {
  return fetch(`${API_BASE_URL}/adapter/sources/${sourceId}/process`, {
    method: "POST",
  }).then((r) => handle<ProcessingJobDetail>(r));
}
