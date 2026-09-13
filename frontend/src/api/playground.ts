// One file that knows how to talk to the /api/playground endpoints.

import type { PlaygroundRequest, PlaygroundRequestInput } from "../types";

const API_BASE_URL = "http://localhost:8000/api";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Request failed (HTTP ${response.status}): ${body}`);
  }
  return response.json();
}

export function askPlayground(data: PlaygroundRequestInput): Promise<PlaygroundRequest> {
  return fetch(`${API_BASE_URL}/playground/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then((r) => handle<PlaygroundRequest>(r));
}

export function getPlaygroundHistory(useCaseId?: number): Promise<PlaygroundRequest[]> {
  const qs = useCaseId ? `?use_case_id=${useCaseId}` : "";
  return fetch(`${API_BASE_URL}/playground/history${qs}`).then((r) =>
    handle<PlaygroundRequest[]>(r),
  );
}
