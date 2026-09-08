// A single, small place that knows how to talk to the backend.
// Every future page (Enterprise Systems, AI Readiness, Governance...)
// will import from a file like this one instead of hardcoding fetch()
// calls all over the UI. That way, if the backend URL ever changes
// (e.g. moving to AWS API Gateway in the optional Phase 2), we change
// it in exactly one place.

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
