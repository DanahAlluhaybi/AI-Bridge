// Company-wide AI Adoption Overview: for every system, whether it's a
// good candidate for AI adoption right now (from its Readiness + Risk
// results) and the single best automation opportunity found for it.
// Ranked by adoption suitability, not plain readiness -- see
// backend/app/adoption/engine.py's get_adoption_overview().

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Badge from "../components/Badge";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { IconArrowRight } from "../components/Icons";
import { getAdoptionOverview } from "../api/adoption";
import type { AdoptionOverviewRow } from "../types";

export default function AIAdoption() {
  const [rows, setRows] = useState<AdoptionOverviewRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdoptionOverview()
      .then((data) => setRows(data.systems))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="AI Adoption"
        description="Two questions, answered per system: can it adopt AI, and if so, where should AI actually be applied first?"
      />

      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && (
        <p className="text-sm text-red-600">
          Could not load AI Adoption data: {error} — is the backend running on port 8000?
        </p>
      )}

      {!loading && !error && rows.length === 0 && (
        <EmptyState
          title="No enterprise systems yet"
          description="Add a system on the Enterprise Systems page to see its AI Adoption outlook here."
        />
      )}

      {!loading && !error && rows.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-sm">
            <thead className="text-left text-xs font-medium text-slate-500">
              <tr>
                <th className="px-5 py-3">System</th>
                <th className="px-5 py-3">Readiness</th>
                <th className="px-5 py-3">Risk</th>
                <th className="px-5 py-3">Adoption</th>
                <th className="px-5 py-3">Top opportunity</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((row) => (
                <tr key={row.system_id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">{row.system_name}</td>
                  <td className="px-5 py-3 text-slate-600">
                    {row.readiness_score === null ? "—" : `${row.readiness_score} / 100`}
                  </td>
                  <td className="px-5 py-3">
                    {row.risk_level === null ? (
                      <span className="text-slate-400">—</span>
                    ) : (
                      <Badge label={row.risk_level} />
                    )}
                  </td>
                  <td className="px-5 py-3">
                    <Badge label={row.decision} />
                  </td>
                  <td className="px-5 py-3 text-slate-600">{row.top_opportunity ?? "—"}</td>
                  <td className="px-5 py-3 text-right">
                    <Link
                      to={`/systems/${row.system_id}`}
                      className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700"
                    >
                      Details <IconArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
