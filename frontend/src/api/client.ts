// A single, small place that knows how to talk to the backend health
// endpoint. Every page imports its API calls from a file like this one
// instead of hardcoding fetch() calls all over the UI, so if the
// backend URL ever changes, it changes in exactly one place.

const API_BASE_URL = "http://localhost:8000/api";

export interface HealthResponse {
  status: string;
  database: string;
  server_time: string;
  total_health_checks_recorded: number;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Backend responded with HTTP ${response.status}`);
  }
  return response.json();
}
