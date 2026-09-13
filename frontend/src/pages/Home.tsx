import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Card from "../components/Card";
import { IconArrowRight, IconBarChart, IconLayers, IconShuffle } from "../components/Icons";
import { listSystems } from "../api/systems";
import { getReadinessSummary } from "../api/readiness";
import { getRiskSummary } from "../api/risk";

const ACTIONS = [
  {
    to: "/systems",
    icon: IconLayers,
    title: "Enterprise Systems",
    description: "See every system AI Bridge knows about, and add new ones.",
  },
  {
    to: "/adapter",
    icon: IconShuffle,
    title: "Legacy-to-AI Adapter",
    description: "Run a system's raw data through cleaning and classification.",
  },
  {
    to: "/dashboard",
    icon: IconBarChart,
    title: "Dashboard",
    description: "Readiness and risk numbers across every assessed system.",
  },
];

const STEPS = [
  { title: "Connect a system", description: "Register an existing system — its owner, data, and how it's integrated." },
  { title: "Run the adapter", description: "Pull its raw data through cleaning, validation, and classification." },
  { title: "Assess readiness & risk", description: "Get a deterministic, explainable score for both, per system." },
];

export default function Home() {
  const [systemsTotal, setSystemsTotal] = useState<number | null>(null);
  const [readinessAssessed, setReadinessAssessed] = useState<number | null>(null);
  const [riskAssessed, setRiskAssessed] = useState<number | null>(null);

  useEffect(() => {
    listSystems()
      .then((systems) => setSystemsTotal(systems.length))
      .catch(() => setSystemsTotal(null));
    getReadinessSummary()
      .then((s) => setReadinessAssessed(s.systems_assessed))
      .catch(() => setReadinessAssessed(null));
    getRiskSummary()
      .then((s) => setRiskAssessed(s.systems_assessed))
      .catch(() => setRiskAssessed(null));
  }, []);

  return (
    <div>
      <div className="mb-10 max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">AI Bridge</h1>
        <p className="mt-2 text-base text-slate-500">
          Making enterprise systems AI-ready without replacing them. AI Bridge
          sits between your existing systems and an AI model, checking data
          quality, risk, and governance before anything is connected.
        </p>
      </div>

      {(systemsTotal !== null || readinessAssessed !== null || riskAssessed !== null) && (
        <div className="mb-10 flex flex-wrap gap-x-10 gap-y-3 border-y border-slate-100 py-4 text-sm">
          <Stat label="Enterprise systems" value={systemsTotal} />
          <Stat label="Readiness-assessed" value={readinessAssessed} />
          <Stat label="Risk-assessed" value={riskAssessed} />
        </div>
      )}

      <div className="mb-10 grid grid-cols-1 gap-4 sm:grid-cols-3">
        {ACTIONS.map(({ to, icon: Icon, title, description }) => (
          <Link key={to} to={to} className="group">
            <Card className="h-full transition-colors group-hover:border-slate-300">
              <Icon className="mb-3 h-5 w-5 text-indigo-600" />
              <p className="text-sm font-semibold text-slate-900">{title}</p>
              <p className="mt-1 text-sm text-slate-500">{description}</p>
              <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-indigo-600">
                Open <IconArrowRight className="h-3.5 w-3.5" />
              </span>
            </Card>
          </Link>
        ))}
      </div>

      <div>
        <h2 className="mb-4 text-sm font-semibold text-slate-900">How it works</h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {STEPS.map((step, i) => (
            <div key={step.title}>
              <p className="text-xs font-medium text-indigo-600">Step {i + 1}</p>
              <p className="mt-1 text-sm font-medium text-slate-900">{step.title}</p>
              <p className="mt-1 text-sm text-slate-500">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | null }) {
  if (value === null) return null;
  return (
    <div className="flex items-baseline gap-1.5">
      <span className="text-lg font-semibold text-slate-900">{value}</span>
      <span className="text-slate-500">{label}</span>
    </div>
  );
}
