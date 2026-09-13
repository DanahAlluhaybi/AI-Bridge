// One file that knows how to talk to the /api/approvals endpoints --
// the Approval Center's data source.

import type { ApprovalDecisionInput, ApprovalRequest } from "../types";

const API_BASE_URL = "http://localhost:8000/api";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Request failed (HTTP ${response.status}): ${body}`);
  }
  return response.json();
}

export function listApprovals(status?: string): Promise<ApprovalRequest[]> {
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  return fetch(`${API_BASE_URL}/approvals${qs}`).then((r) => handle<ApprovalRequest[]>(r));
}

export function decideApproval(
  id: number,
  data: ApprovalDecisionInput,
): Promise<ApprovalRequest> {
  return fetch(`${API_BASE_URL}/approvals/${id}/decide`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then((r) => handle<ApprovalRequest>(r));
}
