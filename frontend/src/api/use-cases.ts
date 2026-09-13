// One file that knows how to talk to the /api/use-cases endpoints,
// same pattern as api/systems.ts.

import type { AIPassport, AIUseCase, AIUseCaseInput } from "../types";

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

export function listUseCases(): Promise<AIUseCase[]> {
  return fetch(`${API_BASE_URL}/use-cases`).then((r) => handle<AIUseCase[]>(r));
}

export function getUseCase(id: number): Promise<AIUseCase> {
  return fetch(`${API_BASE_URL}/use-cases/${id}`).then((r) => handle<AIUseCase>(r));
}

export function createUseCase(data: AIUseCaseInput): Promise<AIUseCase> {
  return fetch(`${API_BASE_URL}/use-cases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then((r) => handle<AIUseCase>(r));
}

export function deleteUseCase(id: number): Promise<void> {
  return fetch(`${API_BASE_URL}/use-cases/${id}`, { method: "DELETE" }).then((r) =>
    handle<void>(r),
  );
}

export function getAIPassport(id: number): Promise<AIPassport> {
  return fetch(`${API_BASE_URL}/use-cases/${id}/passport`).then((r) =>
    handle<AIPassport>(r),
  );
}
