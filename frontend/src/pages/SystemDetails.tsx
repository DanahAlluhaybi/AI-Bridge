// Shows everything AI Bridge knows about one enterprise system. The
// :id in the URL (see App.tsx's route "/systems/:id") is read with
// useParams() and used to fetch that one record.

import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Badge from "../components/Badge";
import { deleteSystem, getSystem } from "../api/systems";
import type { EnterpriseSystem } from "../types";

export default function SystemDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [system, setSystem] = useState<EnterpriseSystem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getSystem(id)
      .then(setSystem)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleDelete() {
    if (!system) return;
    const confirmed = window.confirm(
      `Remove "${system.name}" from AI Bridge? This only removes it from AI Bridge's records.`,
    );
    if (!confirmed) return;

    setDeleting(true);
    try {
      await deleteSystem(system.id);
      navigate("/systems");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete system");
      setDeleting(false);
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  if (error || !system) {
    return (
      <div>
        <BackLink />
        <p className="mt-4 text-sm text-red-600">
          {error ?? "System not found."}
        </p>
      </div>
    );
  }

  return (
    <div>
      <BackLink />

      <div className="mb-6 mt-3 flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold">{system.name}</h2>
          <p className="text-sm text-slate-500">
            {system.system_type} · {system.department}
          </p>
        </div>
        <Badge label={system.status} />
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Section title="Overview">
          <Row label="Name" value={system.name} />
          <Row label="Type" value={system.system_type} />
          <Row label="Department" value={system.department} />
          <Row label="Owner" value={system.owner} />
          <Row label="Status" value={<Badge label={system.status} />} />
        </Section>

        <Section title="Integration">
          <Row label="Integration type" value={system.integration_type} />
          <Row
            label="Connection status"
            value={<Badge label={system.status} />}
          />
          <Row label="Data source" value={system.data_source || "—"} mono />
        </Section>

        <Section title="Data">
          <Row
            label="Data types"
            value={
              system.data_types.length === 0 ? (
                "—"
              ) : (
                <div className="flex flex-wrap justify-end gap-1.5">
                  {system.data_types.map((t) => (
                    <span
                      key={t}
                      className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs text-slate-700"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )
            }
          />
          <Row
            label="Data classification"
            value={<Badge label={system.data_classification} />}
          />
          <Row
            label="Security level"
            value={<Badge label={system.security_level} />}
          />
        </Section>

        <Section title="AI Readiness">
          <p className="text-sm font-medium text-slate-500">
            AI Readiness Assessment — Not assessed yet
          </p>
          <button
            disabled
            title="Coming in Phase 4 — AI Readiness Assessment"
            className="mt-1 w-fit cursor-not-allowed rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-400"
          >
            Assess AI Readiness
          </button>
        </Section>
      </div>

      <div className="mt-8 border-t border-slate-200 pt-6">
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="text-sm font-medium text-red-600 hover:underline disabled:opacity-50"
        >
          {deleting ? "Removing…" : "Remove this system"}
        </button>
      </div>
    </div>
  );
}

function BackLink() {
  return (
    <Link to="/systems" className="text-sm text-slate-500 hover:underline">
      ← Back to Enterprise Systems
    </Link>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </h3>
      <dl className="space-y-3">{children}</dl>
    </div>
  );
}

function Row({
  label,
  value,
  mono,
}: {
  label: string;
  value: ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-4 text-sm">
      <dt className="shrink-0 text-slate-500">{label}</dt>
      <dd
        className={`text-right font-medium text-slate-900 ${
          mono ? "font-mono text-xs" : ""
        }`}
      >
        {value}
      </dd>
    </div>
  );
}
