// A small colored "pill" used all over the Enterprise Systems pages
// for status, data classification, and security level. One component,
// reused everywhere, means the color for "Critical" (for example) is
// defined in exactly one place.

const COLOR_MAP: Record<string, string> = {
  // Status
  Connected: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  Disconnected: "bg-red-50 text-red-700 ring-red-600/20",
  Pending: "bg-amber-50 text-amber-700 ring-amber-600/20",
  // Data classification
  Public: "bg-slate-100 text-slate-700 ring-slate-500/20",
  Internal: "bg-blue-50 text-blue-700 ring-blue-600/20",
  Confidential: "bg-orange-50 text-orange-700 ring-orange-600/20",
  Restricted: "bg-red-50 text-red-700 ring-red-600/20",
  // Security level
  Low: "bg-slate-100 text-slate-700 ring-slate-500/20",
  Medium: "bg-blue-50 text-blue-700 ring-blue-600/20",
  High: "bg-orange-50 text-orange-700 ring-orange-600/20",
  Critical: "bg-red-50 text-red-700 ring-red-600/20",
};

const DEFAULT_COLOR = "bg-slate-100 text-slate-700 ring-slate-500/20";

export default function Badge({ label }: { label: string }) {
  const classes = COLOR_MAP[label] ?? DEFAULT_COLOR;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${classes}`}
    >
      {label}
    </span>
  );
}
