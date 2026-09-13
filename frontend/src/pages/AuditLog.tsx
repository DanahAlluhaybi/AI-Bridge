// The Audit Log (Phase 11): a plain, newest-first trail of everything
// worth recording across the governance flow -- a use case proposed,
// an approval decided, a playground prompt run. Read-only; entries are
// written by audit.log() from inside the routers that make the change.

import { useEffect, useState } from "react";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { getAuditLog } from "../api/audit";
import type { AuditLogEntry } from "../types";

export default function AuditLog() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAuditLog(100)
      .then(setEntries)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="Audit Log"
        description="Every recorded action across AI Bridge's governance flow, newest first."
      />

      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && (
        <p className="text-sm text-red-600">
          Could not load the audit log: {error} — is the backend running on port 8000?
        </p>
      )}

      {!loading && !error && entries.length === 0 && (
        <EmptyState
          title="Nothing recorded yet"
          description="Actions across AI Use Cases, Approvals, and the Playground will show up here as they happen."
        />
      )}

      {!loading && !error && entries.length > 0 && (
        <div className="card divide-y divide-slate-100">
          {entries.map((entry) => (
            <div key={entry.id} className="flex items-start justify-between gap-4 px-5 py-3">
              <div>
                <p className="text-sm text-slate-900">{entry.summary}</p>
                <p className="text-xs text-slate-400">{entry.action}</p>
              </div>
              <span className="shrink-0 text-xs text-slate-400">
                {new Date(entry.created_at).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
