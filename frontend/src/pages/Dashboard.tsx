// Three cards: a backend connection check (calls /api/health), an AI
// Readiness overview, and an AI Risk overview -- both pulled live from
// their summary endpoints so the numbers always reflect real
// assessments, never hardcoded.

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHealth, type HealthResponse } from "../api/client";
import { listApprovals } from "../api/approvals";
import { getReadinessSummary } from "../api/readiness";
import { getRiskSummary } from "../api/risk";
import { listUseCases } from "../api/use-cases";
import Badge from "../components/Badge";
import Card from "../components/Card";
import MetricCard from "../components/MetricCard";
import PageHeader from "../components/PageHeader";
import type { AIUseCase, ApprovalRequest, ReadinessSummary, RiskSummary } from "../types";

type ConnectionState = "checking" | "connected" | "error";

export default function Dashboard() {
  const [state, setState] = useState<ConnectionState>("checking");
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<ReadinessSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [riskSummaryLoading, setRiskSummaryLoading] = useState(true);
  const [riskSummaryError, setRiskSummaryError] = useState<string | null>(null);

  const [useCases, setUseCases] = useState<AIUseCase[]>([]);
  const [pendingApprovals, setPendingApprovals] = useState<ApprovalRequest[]>([]);
  const [governanceLoading, setGovernanceLoading] = useState(true);
  const [governanceError, setGovernanceError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then((res) => {
        setData(res);
        setState("connected");
      })
      .catch((err: Error) => {
        setError(err.message);
        setState("error");
      });

    getReadinessSummary()
      .then(setSummary)
      .catch((err: Error) => setSummaryError(err.message))
      .finally(() => setSummaryLoading(false));

    getRiskSummary()
      .then(setRiskSummary)
      .catch((err: Error) => setRiskSummaryError(err.message))
      .finally(() => setRiskSummaryLoading(false));

    Promise.all([listUseCases(), listApprovals("Pending")])
      .then(([useCaseData, pendingData]) => {
        setUseCases(useCaseData);
        setPendingApprovals(pendingData);
      })
      .catch((err: Error) => setGovernanceError(err.message))
      .finally(() => setGovernanceLoading(false));
  }, []);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Live readiness and risk numbers across every assessed system."
      />

      <div className="space-y-6">
        <Card title="Backend connection">
          <div className="mb-3 flex items-center gap-2">
            <StatusDot state={state} />
            <span className="text-sm text-slate-500">
              {state === "checking" && "Checking connection…"}
              {state === "connected" && "Connected"}
              {state === "error" && "Could not reach the backend API"}
            </span>
          </div>

          {state === "error" && (
            <p className="text-sm text-red-600">
              {error} — make sure the FastAPI server is running on
              http://localhost:8000 (see README.md).
            </p>
          )}

          {state === "connected" && data && (
            <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
              <MetricCard label="Status" value={data.status} />
              <MetricCard label="Database" value={data.database} />
              <MetricCard
                label="Health checks recorded"
                value={String(data.total_health_checks_recorded)}
              />
              <MetricCard
                label="Server time (UTC)"
                value={new Date(data.server_time).toLocaleTimeString()}
              />
            </div>
          )}
        </Card>

        <Card title="AI Readiness overview">
          {summaryLoading && <p className="text-sm text-slate-500">Loading…</p>}
          {summaryError && (
            <p className="text-sm text-red-600">Could not load readiness data: {summaryError}</p>
          )}

          {summary && (
            <>
              <div className="mb-5 grid grid-cols-2 gap-6 sm:grid-cols-5">
                <MetricCard
                  label="Average AI readiness"
                  value={summary.average_score === null ? "—" : `${summary.average_score} / 100`}
                />
                <MetricCard
                  label="Systems assessed"
                  value={`${summary.systems_assessed} / ${summary.systems_total}`}
                />
                <MetricCard label="AI Ready" value={String(summary.ai_ready_count)} />
                <MetricCard
                  label="Needs improvement"
                  value={String(summary.needs_improvement_count)}
                />
                <MetricCard label="Not ready" value={String(summary.not_ready_count)} />
              </div>

              <p className="mb-2 text-xs font-medium text-slate-500">Top governance gaps</p>
              {summary.systems_assessed === 0 ? (
                <p className="text-sm text-slate-500">
                  No systems have been assessed yet — visit a system's details page and click
                  "Assess AI Readiness".
                </p>
              ) : summary.top_governance_gaps.length === 0 ? (
                <p className="text-sm text-slate-500">No governance gaps among assessed systems.</p>
              ) : (
                <ul className="space-y-1.5 text-sm text-slate-600">
                  {summary.top_governance_gaps.map((gap) => (
                    <li key={gap.system_id}>
                      <span className="font-medium text-slate-900">{gap.system_name}</span>{" "}
                      (Governance: {gap.score})
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </Card>

        <Card title="AI Risk overview">
          {riskSummaryLoading && <p className="text-sm text-slate-500">Loading…</p>}
          {riskSummaryError && (
            <p className="text-sm text-red-600">Could not load risk data: {riskSummaryError}</p>
          )}

          {riskSummary && (
            <>
              <div className="mb-5 grid grid-cols-2 gap-6 sm:grid-cols-5">
                <MetricCard
                  label="Average risk score"
                  value={
                    riskSummary.average_risk_score === null
                      ? "—"
                      : `${riskSummary.average_risk_score} / 100`
                  }
                />
                <MetricCard
                  label="Systems assessed"
                  value={`${riskSummary.systems_assessed} / ${riskSummary.systems_total}`}
                />
                <MetricCard label="Low risk" value={String(riskSummary.low_count)} />
                <MetricCard label="High risk" value={String(riskSummary.high_count)} />
                <MetricCard label="Critical risk" value={String(riskSummary.critical_count)} />
              </div>

              <p className="mb-2 text-xs font-medium text-slate-500">Highest risk systems</p>
              {riskSummary.systems_assessed === 0 ? (
                <p className="text-sm text-slate-500">
                  No systems have been risk-assessed yet — visit a system's details page and
                  click "Assess AI Risk".
                </p>
              ) : (
                <ul className="space-y-1.5 text-sm text-slate-600">
                  {riskSummary.highest_risk_systems.map((flag) => (
                    <li key={flag.system_id} className="flex items-center gap-2">
                      <span className="font-medium text-slate-900">{flag.system_name}</span>
                      <Badge label={flag.risk_level} />
                      <span className="text-slate-400">{flag.risk_score} / 100</span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </Card>

        <Card title="AI Governance overview">
          {governanceLoading && <p className="text-sm text-slate-500">Loading…</p>}
          {governanceError && (
            <p className="text-sm text-red-600">
              Could not load governance data: {governanceError}
            </p>
          )}

          {!governanceLoading && !governanceError && (
            <>
              <div className="mb-5 grid grid-cols-2 gap-6 sm:grid-cols-4">
                <MetricCard label="Use cases proposed" value={String(useCases.length)} />
                <MetricCard
                  label="Approved"
                  value={String(useCases.filter((uc) => uc.status === "Approved").length)}
                />
                <MetricCard
                  label="Rejected"
                  value={String(useCases.filter((uc) => uc.status === "Rejected").length)}
                />
                <MetricCard label="Pending approvals" value={String(pendingApprovals.length)} />
              </div>

              {pendingApprovals.length === 0 ? (
                <p className="text-sm text-slate-500">
                  Nothing waiting on a human decision right now.
                </p>
              ) : (
                <>
                  <p className="mb-2 text-xs font-medium text-slate-500">
                    Waiting on a decision
                  </p>
                  <ul className="space-y-1.5 text-sm text-slate-600">
                    {pendingApprovals.slice(0, 5).map((approval) => (
                      <li key={approval.id}>
                        <span className="font-medium text-slate-900">
                          {approval.use_case_name}
                        </span>{" "}
                        — {approval.system_name}
                      </li>
                    ))}
                  </ul>
                  <Link
                    to="/approvals"
                    className="mt-3 inline-block text-sm font-medium text-indigo-600 hover:text-indigo-700"
                  >
                    Go to Approval Center →
                  </Link>
                </>
              )}
            </>
          )}
        </Card>
      </div>
    </div>
  );
}

function StatusDot({ state }: { state: ConnectionState }) {
  const color =
    state === "connected" ? "bg-emerald-500" : state === "error" ? "bg-red-500" : "bg-amber-400";
  return <span className={`h-2 w-2 rounded-full ${color}`} />;
}
