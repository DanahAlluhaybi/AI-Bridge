import type { ReactNode } from "react";

interface Props {
  title?: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

// The one card shape used everywhere: a white surface, a thin border,
// a very light shadow, and consistent internal padding. Pages compose
// this instead of styling a <div> from scratch each time.
export default function Card({ title, description, action, children, className = "" }: Props) {
  return (
    <div className={`card p-6 ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            {title && <h3 className="text-sm font-semibold text-slate-900">{title}</h3>}
            {description && <p className="mt-0.5 text-sm text-slate-500">{description}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
