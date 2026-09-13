// The Approval Center (Phase 9): every ApprovalRequest, filterable by
// status, with a way for a human to approve or reject the ones still
// Pending. Deciding one updates the linked use case's status to match
// in the same step (see backend/app/routers/approvals.py).

import { useEffect, useState } from "react";
import Badge from "../components/Badge";
import Button from "../components/Button";
import Card from "../components/Card";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { decideApproval, listApprovals } from "../api/approvals";
import type { ApprovalRequest } from "../types";

const STATUS_FILTERS = ["Pending", "Approved", "Rejected", "All"] as const;
type StatusFilter = (typeof STATUS_FILTERS)[number];

export default function Approvals() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("Pending");
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [decidingId, setDecidingId] = useState<number | null>(null);
  const [notesById, setNotesById] = useState<Record<number, string>>({});
  const [reviewerName, setReviewerName] = useState("");

  function load() {
    setLoading(true);
    listApprovals(statusFilter === "All" ? undefined : statusFilter)
      .then((data) => {
        setApprovals(data);
        setError(null);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  async function handleDecide(id: number, approve: boolean) {
    if (!reviewerName.trim()) {
      setError("Enter your name before deciding an approval, so the decision records who made it.");
      return;
    }
    setDecidingId(id);
    setError(null);
    try {
      await decideApproval(id, {
        approve,
        decided_by: reviewerName.trim(),
        notes: notesById[id]?.trim() || undefined,
      });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record decision");
    } finally {
      setDecidingId(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Approval Center"
        description="Use cases the governance policy sent for a human decision -- approve or reject each one."
      />

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-slate-500">Your name</span>
          <input
            value={reviewerName}
            onChange={(e) => setReviewerName(e.target.value)}
            className="input max-w-xs"
            placeholder="Recorded as the decider"
          />
        </label>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          className="input w-auto"
        >
          {STATUS_FILTERS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {!loading && approvals.length === 0 && (
        <EmptyState
          title="Nothing here"
          description={
            statusFilter === "Pending"
              ? "No approvals are waiting on a decision right now."
              : `No approvals with status "${statusFilter}" yet.`
          }
        />
      )}

      {!loading && approvals.length > 0 && (
        <div className="space-y-4">
          {approvals.map((approval) => (
            <Card key={approval.id}>
              <div className="mb-2 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-900">{approval.use_case_name}</p>
                  <p className="text-xs text-slate-400">{approval.system_name}</p>
                </div>
                <Badge label={approval.status} />
              </div>
              <p className="mb-3 text-sm text-slate-600">{approval.reason}</p>

              {approval.status !== "Pending" ? (
                <p className="text-xs text-slate-400">
                  {approval.status} by {approval.decided_by ?? "unknown"}
                  {approval.decided_at && ` on ${new Date(approval.decided_at).toLocaleString()}`}
                  {approval.decision_notes && ` — "${approval.decision_notes}"`}
                </p>
              ) : (
                <div className="flex flex-wrap items-center gap-3">
                  <input
                    value={notesById[approval.id] ?? ""}
                    onChange={(e) =>
                      setNotesById({ ...notesById, [approval.id]: e.target.value })
                    }
                    className="input max-w-sm"
                    placeholder="Notes (optional)"
                  />
                  <Button
                    onClick={() => handleDecide(approval.id, true)}
                    disabled={decidingId === approval.id}
                  >
                    {decidingId === approval.id ? "Recording…" : "Approve"}
                  </Button>
                  <Button
                    variant="danger-ghost"
                    onClick={() => handleDecide(approval.id, false)}
                    disabled={decidingId === approval.id}
                  >
                    Reject
                  </Button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
