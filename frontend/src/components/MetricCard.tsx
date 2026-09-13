interface Props {
  label: string;
  value: string;
  hint?: string;
}

// One number, plainly labeled. Used in the metric grids on the
// Dashboard rather than wrapping every stat in a full Card.
export default function MetricCard({ label, value, hint }: Props) {
  return (
    <div>
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-slate-400">{hint}</p>}
    </div>
  );
}
