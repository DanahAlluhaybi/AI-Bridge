// A small status tag, reused across every page for connection status,
// data classification, security level, adapter classification, and
// readiness/risk levels. One component means "High" always looks the
// same regardless of which field it's labeling.

const COLOR_MAP: Record<string, string> = {
  // Status
  Connected: "bg-emerald-50 text-emerald-700",
  Disconnected: "bg-red-50 text-red-700",
  Pending: "bg-amber-50 text-amber-700",
  // Data classification
  Public: "bg-slate-100 text-slate-600",
  Internal: "bg-blue-50 text-blue-700",
  Confidential: "bg-orange-50 text-orange-700",
  Restricted: "bg-red-50 text-red-700",
  // Security level (and, sharing the same labels, AI Risk level)
  Low: "bg-slate-100 text-slate-600",
  Medium: "bg-blue-50 text-blue-700",
  High: "bg-orange-50 text-orange-700",
  Critical: "bg-red-50 text-red-700",
  // Adapter data classification
  Sensitive: "bg-red-50 text-red-700",
  Info: "bg-slate-100 text-slate-600",
  Warning: "bg-amber-50 text-amber-700",
  // AI Readiness levels
  "AI Ready": "bg-emerald-50 text-emerald-700",
  "Mostly Ready": "bg-blue-50 text-blue-700",
  "Needs Improvement": "bg-amber-50 text-amber-700",
  "Not Ready": "bg-red-50 text-red-700",
  // AI Adoption decisions
  "Good Candidate": "bg-emerald-50 text-emerald-700",
  Conditional: "bg-blue-50 text-blue-700",
  "Not Yet": "bg-amber-50 text-amber-700",
  "Not Recommended": "bg-red-50 text-red-700",
  "Insufficient Information": "bg-slate-100 text-slate-500",
  // AI Use Case status
  Proposed: "bg-amber-50 text-amber-700",
  Approved: "bg-emerald-50 text-emerald-700",
  Rejected: "bg-red-50 text-red-700",
  // Policy decision (ALLOW / HUMAN_APPROVAL / BLOCK)
  ALLOW: "bg-emerald-50 text-emerald-700",
  HUMAN_APPROVAL: "bg-amber-50 text-amber-700",
  BLOCK: "bg-red-50 text-red-700",
  // Approval request status reuses "Pending" from Status above.
};

const DEFAULT_COLOR = "bg-slate-100 text-slate-600";

export default function Badge({ label }: { label: string }) {
  const classes = COLOR_MAP[label] ?? DEFAULT_COLOR;
  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${classes}`}
    >
      {label}
    </span>
  );
}
