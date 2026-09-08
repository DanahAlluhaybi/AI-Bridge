// New in Phase 2. Phase 1 had exactly one page, so Dashboard.tsx drew
// its own header. Now that we have more than one page, that header
// (and the navigation between pages) is pulled out into a shared
// Layout so every page looks consistent and we don't repeat ourselves.
//
// <Outlet /> is react-router-dom's way of saying "render whichever
// page matched the current URL, right here" -- see App.tsx for how
// routes are wired to this layout.

import type { ReactNode } from "react";
import { NavLink, Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              AI Bridge
            </h1>
            <p className="text-xs text-slate-500">
              Making Enterprise Systems AI-Ready Without Replacing Them
            </p>
          </div>
          <nav className="flex gap-1 text-sm font-medium">
            <NavTab to="/">Dashboard</NavTab>
            <NavTab to="/systems">Enterprise Systems</NavTab>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}

function NavTab({ to, children }: { to: string; children: ReactNode }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        `rounded-md px-3 py-2 transition-colors ${
          isActive
            ? "bg-slate-900 text-white"
            : "text-slate-600 hover:bg-slate-100"
        }`
      }
    >
      {children}
    </NavLink>
  );
}
