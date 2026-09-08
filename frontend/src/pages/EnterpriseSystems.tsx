// The main Phase 2 page: a table of every enterprise system AI Bridge
// knows about, with search, two filters, and a way to add a new one.

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Badge from "../components/Badge";
import AddSystemModal from "../components/AddSystemModal";
import { listSystems } from "../api/systems";
import type { EnterpriseSystem, IntegrationType, SystemStatus } from "../types";
import { INTEGRATION_TYPES, SYSTEM_STATUSES } from "../types";

export default function EnterpriseSystems() {
  const [systems, setSystems] = useState<EnterpriseSystem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<SystemStatus | "">("");
  const [integrationFilter, setIntegrationFilter] = useState<
    IntegrationType | ""
  >("");
  const [showAddModal, setShowAddModal] = useState(false);

  function loadSystems() {
    setLoading(true);
    listSystems()
      .then((data) => {
        setSystems(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadSystems();
  }, []);

  // We fetch the full list once, then filter it here in the browser.
  // With five systems this is instant and avoids a network round-trip
  // on every keystroke. (The backend also supports these same filters
  // as query parameters -- see routers/systems.py -- for when the
  // dataset is too large to ship to the browser all at once.)
  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return systems.filter((system) => {
      const matchesSearch =
        term === "" ||
        system.name.toLowerCase().includes(term) ||
        system.department.toLowerCase().includes(term);
      const matchesStatus = statusFilter === "" || system.status === statusFilter;
      const matchesIntegration =
        integrationFilter === "" || system.integration_type === integrationFilter;
      return matchesSearch && matchesStatus && matchesIntegration;
    });
  }, [systems, search, statusFilter, integrationFilter]);

  return (
    <div>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h2 className="text-lg font-medium">Enterprise Systems</h2>
          <p className="text-sm text-slate-500">
            Existing systems AI Bridge can connect to — nothing here is
            replaced, only observed and assessed.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          + Add System
        </button>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Search by name or department…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input max-w-xs"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as SystemStatus | "")}
          className="input w-auto"
        >
          <option value="">All statuses</option>
          {SYSTEM_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={integrationFilter}
          onChange={(e) =>
            setIntegrationFilter(e.target.value as IntegrationType | "")
          }
          className="input w-auto"
        >
          <option value="">All integration types</option>
          {INTEGRATION_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <p className="text-sm text-slate-500">Loading enterprise systems…</p>
      )}
      {error && (
        <p className="text-sm text-red-600">
          Could not load systems: {error} — is the backend running on port
          8000?
        </p>
      )}

      {!loading && !error && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Department</th>
                <th className="px-4 py-3">Integration</th>
                <th className="px-4 py-3">Data Classification</th>
                <th className="px-4 py-3">Security</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((system) => (
                <tr key={system.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium">{system.name}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {system.system_type}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {system.department}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {system.integration_type}
                  </td>
                  <td className="px-4 py-3">
                    <Badge label={system.data_classification} />
                  </td>
                  <td className="px-4 py-3">
                    <Badge label={system.security_level} />
                  </td>
                  <td className="px-4 py-3">
                    <Badge label={system.status} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/systems/${system.id}`}
                      className="font-medium text-slate-700 hover:text-slate-900 hover:underline"
                    >
                      View Details →
                    </Link>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                    No systems match your filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showAddModal && (
        <AddSystemModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => {
            setShowAddModal(false);
            loadSystems();
          }}
        />
      )}
    </div>
  );
}
