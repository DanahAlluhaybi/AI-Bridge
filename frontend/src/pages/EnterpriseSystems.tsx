// A table of every enterprise system AI Bridge knows about, with
// search, two filters, and a way to add a new one.

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Badge from "../components/Badge";
import Button from "../components/Button";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import AddSystemModal from "../components/AddSystemModal";
import { IconArrowRight, IconPlus } from "../components/Icons";
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
      <PageHeader
        title="Enterprise Systems"
        description="Existing systems AI Bridge can connect to — nothing here is replaced, only observed and assessed."
        action={
          <Button onClick={() => setShowAddModal(true)}>
            <IconPlus className="h-4 w-4" />
            Add system
          </Button>
        }
      />

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

      {!loading && !error && filtered.length === 0 && (
        <EmptyState
          title="No systems match your filters"
          description="Try a different search term, or clear the status and integration filters."
        />
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-sm">
            <thead className="text-left text-xs font-medium text-slate-500">
              <tr>
                <th className="px-5 py-3">Name</th>
                <th className="px-5 py-3">Type</th>
                <th className="px-5 py-3">Department</th>
                <th className="px-5 py-3">Integration</th>
                <th className="px-5 py-3">Data Classification</th>
                <th className="px-5 py-3">Security</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((system) => (
                <tr key={system.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3 font-medium text-slate-900">{system.name}</td>
                  <td className="px-5 py-3 text-slate-600">
                    {system.system_type}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {system.department}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {system.integration_type}
                  </td>
                  <td className="px-5 py-3">
                    <Badge label={system.data_classification} />
                  </td>
                  <td className="px-5 py-3">
                    <Badge label={system.security_level} />
                  </td>
                  <td className="px-5 py-3">
                    <Badge label={system.status} />
                  </td>
                  <td className="px-5 py-3 text-right">
                    <Link
                      to={`/systems/${system.id}`}
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
