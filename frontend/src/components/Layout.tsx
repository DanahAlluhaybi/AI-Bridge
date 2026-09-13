import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  IconBarChart,
  IconClipboard,
  IconClose,
  IconHome,
  IconLayers,
  IconMenu,
  IconPlay,
  IconScroll,
  IconShieldCheck,
  IconShuffle,
  IconTarget,
} from "./Icons";

const NAV_ITEMS = [
  { to: "/", label: "Home", icon: IconHome, end: true },
  { to: "/dashboard", label: "Dashboard", icon: IconBarChart, end: false },
  { to: "/systems", label: "Enterprise Systems", icon: IconLayers, end: false },
  { to: "/adapter", label: "Data Adapter", icon: IconShuffle, end: false },
  { to: "/adoption", label: "AI Adoption", icon: IconTarget, end: false },
  { to: "/use-cases", label: "AI Use Cases", icon: IconClipboard, end: false },
  { to: "/approvals", label: "Approval Center", icon: IconShieldCheck, end: false },
  { to: "/playground", label: "AI Playground", icon: IconPlay, end: false },
  { to: "/audit-log", label: "Audit Log", icon: IconScroll, end: false },
];

export default function Layout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white text-slate-900 md:flex">
      {/* Mobile top bar -- the sidebar below is hidden until this opens it. */}
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 md:hidden">
        <Wordmark />
        <button
          onClick={() => setMobileNavOpen(true)}
          className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100"
          aria-label="Open navigation"
        >
          <IconMenu className="h-5 w-5" />
        </button>
      </div>

      {mobileNavOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-slate-900/30"
            onClick={() => setMobileNavOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 w-64 bg-white p-4 shadow-popover">
            <div className="mb-6 flex items-center justify-between">
              <Wordmark />
              <button
                onClick={() => setMobileNavOpen(false)}
                className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100"
                aria-label="Close navigation"
              >
                <IconClose className="h-5 w-5" />
              </button>
            </div>
            <Nav onNavigate={() => setMobileNavOpen(false)} />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 border-r border-slate-200 md:flex md:flex-col md:justify-between md:px-4 md:py-5">
        <div>
          <div className="mb-6 px-2">
            <Wordmark />
          </div>
          <Nav />
        </div>
        <p className="px-2 text-xs text-slate-400">Local development</p>
      </aside>

      <main className="min-w-0 flex-1">
        <div className="mx-auto max-w-6xl px-6 py-8 md:px-10">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function Wordmark() {
  return (
    <div className="flex items-center gap-2">
      <span className="h-2 w-2 rounded-full bg-indigo-600" />
      <span className="text-base font-semibold tracking-tight">AI Bridge</span>
    </div>
  );
}

function Nav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="space-y-0.5">
      {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors ${
              isActive
                ? "bg-indigo-50 text-indigo-700"
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
            }`
          }
        >
          <Icon className="h-[18px] w-[18px] shrink-0" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
