// Unchanged logic from Phase 1 -- still just calls /api/health and
// shows the result. The only difference is this file no longer draws
// its own <header>: that moved into components/Layout.tsx once we had
// more than one page to share it with.

import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "../api/client";

type ConnectionState = "checking" | "connected" | "error";

export default function Dashboard() {
  const [state, setState] = useState<ConnectionState>("checking");
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then((res) => {
        setData(res);
        setState("connected");
      })
      .catch((err: Error) => {
        setError(err.message);
        setState("error");
      });
  }, []);

  return (
    <div>
      <h2 className="mb-1 text-lg font-medium">Dashboard</h2>
      <p className="mb-6 text-sm text-slate-500">
        Phase 2 — Foundation + Enterprise Systems. Still no governance,
        risk, or AI logic — that starts in later phases.
      </p>

      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center gap-2">
          <StatusDot state={state} />
          <span className="font-medium">Backend connection</span>
        </div>

        {state === "checking" && (
          <p className="text-sm text-slate-500">
            Checking connection to the backend…
          </p>
        )}

        {state === "error" && (
          <div className="text-sm text-red-600">
            <p>Could not reach the backend API.</p>
            <p className="mt-1 text-red-400">{error}</p>
            <p className="mt-2 text-slate-500">
              Make sure the FastAPI server is running on
              http://localhost:8000 (see README.md).
            </p>
          </div>
        )}

        {state === "connected" && data && (
          <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <Metric label="Status" value={data.status} />
            <Metric label="Database" value={data.database} />
            <Metric
              label="Health checks recorded"
              value={String(data.total_health_checks_recorded)}
            />
            <Metric
              label="Server time (UTC)"
              value={new Date(data.server_time).toLocaleTimeString()}
            />
          </dl>
        )}
      </div>
    </div>
  );
}

function StatusDot({ state }: { state: ConnectionState }) {
  const color =
    state === "connected"
      ? "bg-emerald-500"
      : state === "error"
        ? "bg-red-500"
        : "bg-amber-400";
  return <span className={`h-2.5 w-2.5 rounded-full ${color}`} />;
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-400">
        {label}
      </dt>
      <dd className="mt-1 font-medium">{value}</dd>
    </div>
  );
}
