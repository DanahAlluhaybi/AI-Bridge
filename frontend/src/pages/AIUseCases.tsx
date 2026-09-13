// Every proposed AI Use Case, with the governance policy decision it
// received at proposal time (see backend/app/use_cases/policy.py) and
// the status that decision produced -- ALLOW/BLOCK settle the status
// immediately, HUMAN_APPROVAL leaves it Proposed until someone decides
// in the Approval Center.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AddUseCaseModal from "../components/AddUseCaseModal";
import Badge from "../components/Badge";
import Button from "../components/Button";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { IconArrowRight, IconPlus } from "../components/Icons";
import { deleteUseCase, listUseCases } from "../api/use-cases";
import type { AIUseCase } from "../types";

export default function AIUseCases() {
  const [useCases, setUseCases] = useState<AIUseCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  function load() {
    setLoading(true);
    listUseCases()
      .then((data) => {
        setUseCases(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleDelete(id: number) {
    setDeletingId(id);
    try {
      await deleteUseCase(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete use case");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="AI Use Cases"
        description="Every proposed use of AI, and the governance decision it received: allowed outright, sent for human approval, or blocked."
        action={
          <Button onClick={() => setShowAddModal(true)}>
            <IconPlus className="h-4 w-4" />
            Propose use case
          </Button>
        }
      />

      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && (
        <p className="text-sm text-red-600">
          Could not load use cases: {error} — is the backend running on port 8000?
        </p>
      )}

      {!loading && !error && useCases.length === 0 && (
        <EmptyState
          title="No use cases proposed yet"
          description="Propose one against an enterprise system to see how it's governed."
        />
      )}

      {!loading && !error && useCases.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-sm">
            <thead className="text-left text-xs font-medium text-slate-500">
              <tr>
                <th className="px-5 py-3">Use case</th>
                <th className="px-5 py-3">System</th>
                <th className="px-5 py-3">Automation level</th>
                <th className="px-5 py-3">Policy</th>
                <th className="px-5 py-3">Status</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {useCases.map((uc) => (
                <tr key={uc.id} className="hover:bg-slate-50">
                  <td className="px-5 py-3">
                    <p className="font-medium text-slate-900">{uc.name}</p>
                    <p className="text-xs text-slate-400">{uc.owner}</p>
                  </td>
                  <td className="px-5 py-3 text-slate-600">{uc.system_name}</td>
                  <td className="px-5 py-3 text-slate-600">{uc.requested_automation_level}</td>
                  <td className="px-5 py-3">
                    <Badge label={uc.policy_decision} />
                  </td>
                  <td className="px-5 py-3">
                    <Badge label={uc.status} />
                  </td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex items-center justify-end gap-4">
                      <Link
                        to={`/use-cases/${uc.id}/passport`}
                        className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700"
                      >
                        AI Passport <IconArrowRight className="h-3.5 w-3.5" />
                      </Link>
                      <button
                        onClick={() => handleDelete(uc.id)}
                        disabled={deletingId === uc.id}
                        className="text-sm font-medium text-slate-400 hover:text-red-600"
                      >
                        {deletingId === uc.id ? "Removing…" : "Remove"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAddModal && (
        <AddUseCaseModal
          onClose={() => setShowAddModal(false)}
          onCreated={() => {
            setShowAddModal(false);
            load();
          }}
        />
      )}
    </div>
  );
}
