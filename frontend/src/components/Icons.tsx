// A small set of hand-drawn line icons, shared across the sidebar and
// a few pages. Kept as plain inline SVG (no icon package) so nothing
// here depends on npm registry access at build time.

type IconProps = {
  className?: string;
};

const base = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function IconHome({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M4 10.5 12 4l8 6.5" />
      <path d="M6 9.5V20h12V9.5" />
      <path d="M10 20v-6h4v6" />
    </svg>
  );
}

export function IconLayers({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M12 3.5 4 8l8 4.5L20 8Z" />
      <path d="m4 12 8 4.5L20 12" />
      <path d="m4 16 8 4.5L20 16" />
    </svg>
  );
}

export function IconShuffle({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M4 7h3.5c2 0 3 1 4.5 3" />
      <path d="M4 17h3.5c2 0 3-1 4.5-3" />
      <path d="M16 7h4M16 17h4" />
      <path d="m17.5 5 2.5 2-2.5 2M17.5 15l2.5 2-2.5 2" />
    </svg>
  );
}

export function IconBarChart({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M5 19V10M12 19V5M19 19v-6" />
      <path d="M3 19h18" />
    </svg>
  );
}

export function IconPlus({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function IconArrowRight({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export function IconTarget({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    </svg>
  );
}

export function IconClipboard({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <rect x="6" y="4.5" width="12" height="17" rx="1.5" />
      <path d="M9 4.5V3.5A1.5 1.5 0 0 1 10.5 2h3A1.5 1.5 0 0 1 15 3.5v1" />
      <path d="M9 11h6M9 14.5h6M9 17.5h3.5" />
    </svg>
  );
}

export function IconShieldCheck({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M12 3 5 6v5.5c0 4.2 3 7.4 7 9 4-1.6 7-4.8 7-9V6Z" />
      <path d="m9 12 2 2 4-4.5" />
    </svg>
  );
}

export function IconPlay({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M10.5 8.5v7l6-3.5Z" />
    </svg>
  );
}

export function IconScroll({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M6 4h11a2 2 0 0 1 2 2v13a1.5 1.5 0 0 1-3 0V6a1 1 0 0 0-1-1H6a2 2 0 0 0-2 2v11.5A1.5 1.5 0 0 0 5.5 20H16" />
      <path d="M8 9h7M8 12.5h7" />
    </svg>
  );
}

export function IconMenu({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  );
}

export function IconClose({ className }: IconProps) {
  return (
    <svg {...base} className={className}>
      <path d="M6 6l12 12M18 6 6 18" />
    </svg>
  );
}
