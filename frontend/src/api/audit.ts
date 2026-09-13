// One file that knows how to talk to the /api/audit-log endpoint.

import type { AuditLogEntry } from "../types";

const API_BASE_URL = "http://localhost:8000/api";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Request failed (HTTP ${response.status}): ${body}`);
  }
  return response.json();
}

export function getAuditLog(limit = 50): Promise<AuditLogEntry[]> {
  return fetch(`${API_BASE_URL}/audit-log?limit=${limit}`).then((r) =>
    handle<AuditLogEntry[]>(r),
  );
}
