// Shows everything AI Bridge knows about one enterprise system. The
// :id in the URL (see App.tsx's route "/systems/:id") is read with
// useParams() and used to fetch that one record.
//
// The "AI Readiness" and "AI Risk" sections each fetch whatever
// assessment already exists for this system, and their buttons run a
// brand-new one (see backend/app/readiness/engine.py and
// backend/app/risk/engine.py).

import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Badge from "../components/Badge";
import Button from "../components/Button";
import Card from "../components/Card";
import { IconArrowRight } from "../components/Icons";
import { deleteSystem, getSystem } from "../api/systems";
import {
  assessSystem,
  getAssessmentHistory,
  getLatestAssessment,
} from "../api/readiness";
import {
  assessRisk,
  getLatestRiskAssessment,
  getRiskAssessmentHistory,
} from "../api/risk";
import { getSystemAdoption } from "../api/adoption";
import { DIMENSION_ORDER, RISK_FACTOR_ORDER } from "../types";
import type {
  AIReadinessAssessment,
  AIRiskAssessment,
  AutomationOpportunity,
  EnterpriseSystem,
  SystemAdoption,
} from "../types";

export default function SystemDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [system, setSystem] = useState<EnterpriseSystem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const [assessment, setAssessment] = useState<AIReadinessAssessment | null>(null);
  const [loadingAssessment, setLoadingAssessment] = useState(true);
  const [assessing, setAssessing] = useState(false);
  const [assessError, setAssessError] = useState<string | null>(null);

  const [riskAssessment, setRiskAssessment] = useState<AIRiskAssessment | null>(null);
  const [loadingRisk, setLoadingRisk] = useState(true);
  const [assessingRisk, setAssessingRisk] = useState(false);
  const [riskError, setRiskError] = useState<string | null>(null);

  const [adoption, setAdoption] = useState<SystemAdoption | null>(null);
  const [loadingAdoption, setLoadingAdoption] = useState(true);
  const [adoptionError, setAdoptionError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getSystem(id)
      .then(setSystem)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));

    setLoadingAssessment(true);
    getLatestAssessment(Number(id))
      .then(setAssessment)
      .catch(() => setAssessment(null))
      .finally(() => setLoadingAssessment(false));

    setLoadingRisk(true);
    getLatestRiskAssessment(Number(id))
      .then(setRiskAssessment)
      .catch(() => setRiskAssessment(null))
      .finally(() => setLoadingRisk(false));

    setLoadingAdoption(true);
    setAdoptionError(null);
    getSystemAdoption(Number(id))
      .then(setAdoption)
      .catch((err: Error) => setAdoptionError(err.message))
      .finally(() => setLoadingAdoption(false));
  }, [id]);

  async function handleDelete() {
    if (!system) return;
    const confirmed = window.confirm(
      `Remove "${system.name}" from AI Bridge? This only removes it from AI Bridge's records.`,
    );
    if (!confirmed) return;

    setDeleting(true);
    try {
      await deleteSystem(system.id);
      navigate("/systems");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete system");
      setDeleting(false);
    }
  }

  // Re-fetches the AI Adoption decision after Readiness or Risk
  // changes -- the decision is always a live read of both (see
  // backend/app/adoption/engine.py), so it can't stay correct on its
  // own once either one moves.
  function refreshAdoption(systemId: number) {
    getSystemAdoption(systemId)
      .then(setAdoption)
      .catch(() => {});
  }

  function handleAssess() {
    if (!system) return;
    setAssessing(true);
    setAssessError(null);
    assessSystem(system.id)
      .then((result) => {
        setAssessment(result);
        refreshAdoption(system.id);
      })
      .catch((err: Error) => setAssessError(err.message))
      .finally(() => setAssessing(false));
  }

  function handleAssessRisk() {
    if (!system) return;
    setAssessingRisk(true);
    setRiskError(null);
    assessRisk(system.id)
      .then((result) => {
        setRiskAssessment(result);
        refreshAdoption(system.id);
      })
      .catch((err: Error) => setRiskError(err.message))
      .finally(() => setAssessingRisk(false));
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  if (error || !system) {
    return (
      <div>
        <BackLink />
        <p className="mt-4 text-sm text-red-600">{error ?? "System not found."}</p>
      </div>
    );
  }

  return (
    <div>
      <BackLink />

      <div className="mb-6 mt-3 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{system.name}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {system.system_type} · {system.department}
          </p>
        </div>
        <Badge label={system.status} />
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card title="Overview">
          <dl className="space-y-3">
            <Row label="Name" value={system.name} />
            <Row label="Type" value={system.system_type} />
            <Row label="Department" value={system.department} />
            <Row label="Owner" value={system.owner} />
            <Row label="Status" value={<Badge label={system.status} />} />
          </dl>
        </Card>

        <Card title="Integration">
          <dl className="space-y-3">
            <Row label="Integration type" value={system.integration_type} />
            <Row label="Connection status" value={<Badge label={system.status} />} />
            <Row label="Data source" value={system.data_source || "—"} mono />
          </dl>
        </Card>

        <Card title="Data">
          <dl className="space-y-3">
            <Row
              label="Data types"
              value={
                system.data_types.length === 0 ? (
                  "—"
                ) : (
                  <div className="flex flex-wrap justify-end gap-1.5">
                    {system.data_types.map((t) => (
                      <span
                        key={t}
                        className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )
              }
            />
            <Row label="Data classification" value={<Badge label={system.data_classification} />} />
            <Row label="Security level" value={<Badge label={system.security_level} />} />
          </dl>
        </Card>

        <Card title="AI Readiness">
          <ReadinessPanel
            systemId={system.id}
            assessment={assessment}
            loading={loadingAssessment}
            assessing={assessing}
            error={assessError}
            onAssess={handleAssess}
          />
        </Card>

        <Card title="AI Risk">
          <RiskPanel
            systemId={system.id}
            assessment={riskAssessment}
            loading={loadingRisk}
            assessing={assessingRisk}
            error={riskError}
            onAssess={handleAssessRisk}
          />
        </Card>

        <Card title="AI Adoption" className="md:col-span-2">
          <AdoptionPanel adoption={adoption} loading={loadingAdoption} error={adoptionError} />
        </Card>
      </div>

      <div className="mt-8 border-t border-slate-100 pt-6">
        <Button variant="danger-ghost" onClick={handleDelete} disabled={deleting}>
          {deleting ? "Removing…" : "Remove this system"}
        </Button>
      </div>
    </div>
  );
}

function ReadinessPanel({
  systemId,
  assessment,
  loading,
  assessing,
  error,
  onAssess,
}: {
  systemId: number;
  assessment: AIReadinessAssessment | null;
  loading: boolean;
  assessing: boolean;
  error: string | null;
  onAssess: () => void;
}) {
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<AIReadinessAssessment[] | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  function toggleHistory() {
    const next = !showHistory;
    setShowHistory(next);
    if (next && history === null) {
      setLoadingHistory(true);
      getAssessmentHistory(systemId)
        .then(setHistory)
        .finally(() => setLoadingHistory(false));
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  return (
    <div>
      {!assessment && (
        <p className="mb-3 text-sm font-medium text-slate-500">Not assessed yet</p>
      )}

      {assessment && (
        <div className="mb-4">
          <div className="mb-1 flex items-baseline gap-2">
            <span className="text-2xl font-semibold text-slate-900">{assessment.overall_score}</span>
            <span className="text-sm text-slate-400">/ 100</span>
            <Badge label={assessment.readiness_level} />
          </div>
          <p className="text-xs text-slate-400">
            Assessed {new Date(assessment.created_at).toLocaleString()}
          </p>
        </div>
      )}

      <Button variant="secondary" onClick={onAssess} disabled={assessing} className="mb-4">
        {assessing ? "Assessing…" : assessment ? "Re-assess AI Readiness" : "Assess AI Readiness"}
      </Button>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {assessment && (
        <>
          <div className="mb-4 space-y-2">
            {DIMENSION_ORDER.map((dimension) => (
              <DimensionBar
                key={dimension}
                label={dimension}
                score={assessment.dimension_scores[dimension] ?? 0}
              />
            ))}
          </div>

          {assessment.identified_gaps.length > 0 && (
            <div className="mb-4">
              <p className="mb-1 text-xs font-medium text-slate-500">Gaps</p>
              <ul className="space-y-1 text-sm text-slate-600">
                {assessment.identified_gaps.map((gap) => (
                  <li key={gap.dimension}>
                    <span className="font-medium text-slate-900">{gap.dimension}</span> ({gap.score}) —{" "}
                    {gap.description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {assessment.recommendations.length > 0 && (
            <div className="mb-4">
              <p className="mb-1 text-xs font-medium text-slate-500">Recommendations</p>
              <ul className="list-disc space-y-1 pl-4 text-sm text-slate-600">
                {assessment.recommendations.map((rec) => (
                  <li key={rec}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={toggleHistory}
            className="text-xs font-medium text-slate-500 hover:text-slate-700"
          >
            {showHistory ? "Hide past assessments" : "View past assessments"}
          </button>

          {showHistory && (
            <div className="mt-2 space-y-1 border-t border-slate-100 pt-2">
              {loadingHistory && <p className="text-xs text-slate-400">Loading…</p>}
              {history && history.length === 0 && (
                <p className="text-xs text-slate-400">No past assessments.</p>
              )}
              {history &&
                history.map((a) => (
                  <div key={a.id} className="flex items-center justify-between text-xs text-slate-500">
                    <span>{new Date(a.created_at).toLocaleString()}</span>
                    <span className="flex items-center gap-1.5">
                      {a.overall_score} / 100
                      <Badge label={a.readiness_level} />
                    </span>
                  </div>
                ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Below WEAK_DIMENSION_THRESHOLD (70, same constant the backend uses
// to decide gaps) the bar reads amber/red instead of slate/green, so a
// weak dimension is visible before you even read the gaps list below.
function barColor(score: number): string {
  if (score >= 90) return "bg-emerald-500";
  if (score >= 70) return "bg-blue-500";
  if (score >= 50) return "bg-amber-500";
  return "bg-red-500";
}

function DimensionBar({ label, score }: { label: string; score: number }) {
  return (
    <div>
      <div className="mb-0.5 flex items-center justify-between text-xs">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-700">{score}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${barColor(score)}`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

function RiskPanel({
  systemId,
  assessment,
  loading,
  assessing,
  error,
  onAssess,
}: {
  systemId: number;
  assessment: AIRiskAssessment | null;
  loading: boolean;
  assessing: boolean;
  error: string | null;
  onAssess: () => void;
}) {
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<AIRiskAssessment[] | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  function toggleHistory() {
    const next = !showHistory;
    setShowHistory(next);
    if (next && history === null) {
      setLoadingHistory(true);
      getRiskAssessmentHistory(systemId)
        .then(setHistory)
        .finally(() => setLoadingHistory(false));
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  return (
    <div>
      {!assessment && (
        <p className="mb-3 text-sm font-medium text-slate-500">Not risk-assessed yet</p>
      )}

      {assessment && (
        <div className="mb-4">
          <div className="mb-1 flex items-baseline gap-2">
            <span className="text-2xl font-semibold text-slate-900">{assessment.risk_score}</span>
            <span className="text-sm text-slate-400">/ 100</span>
            <Badge label={assessment.risk_level} />
          </div>
          <p className="text-xs text-slate-400">
            Assessed {new Date(assessment.created_at).toLocaleString()}
          </p>
        </div>
      )}

      <Button variant="secondary" onClick={onAssess} disabled={assessing} className="mb-4">
        {assessing ? "Assessing…" : assessment ? "Re-assess AI Risk" : "Assess AI Risk"}
      </Button>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {assessment && (
        <>
          <div className="mb-4 space-y-2">
            {RISK_FACTOR_ORDER.map((factor) => (
              <RiskFactorBar
                key={factor}
                label={factor}
                score={assessment.risk_factors[factor] ?? 0}
              />
            ))}
          </div>

          {assessment.risk_drivers.length > 0 && (
            <div className="mb-4">
              <p className="mb-1 text-xs font-medium text-slate-500">Risk drivers</p>
              <ul className="space-y-1 text-sm text-slate-600">
                {assessment.risk_drivers.map((driver) => (
                  <li key={driver.factor}>
                    <span className="font-medium text-slate-900">{driver.factor}</span> ({driver.score}) —{" "}
                    {driver.description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={toggleHistory}
            className="text-xs font-medium text-slate-500 hover:text-slate-700"
          >
            {showHistory ? "Hide past assessments" : "View past assessments"}
          </button>

          {showHistory && (
            <div className="mt-2 space-y-1 border-t border-slate-100 pt-2">
              {loadingHistory && <p className="text-xs text-slate-400">Loading…</p>}
              {history && history.length === 0 && (
                <p className="text-xs text-slate-400">No past assessments.</p>
              )}
              {history &&
                history.map((a) => (
                  <div key={a.id} className="flex items-center justify-between text-xs text-slate-500">
                    <span>{new Date(a.created_at).toLocaleString()}</span>
                    <span className="flex items-center gap-1.5">
                      {a.risk_score} / 100
                      <Badge label={a.risk_level} />
                    </span>
                  </div>
                ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Higher is riskier here, the opposite of DimensionBar's readiness
// scores, so the color scale runs the other direction too.
function riskBarColor(score: number): string {
  if (score >= 75) return "bg-red-500";
  if (score >= 50) return "bg-orange-500";
  if (score >= 25) return "bg-amber-500";
  return "bg-emerald-500";
}

function RiskFactorBar({ label, score }: { label: string; score: number }) {
  return (
    <div>
      <div className="mb-0.5 flex items-center justify-between text-xs">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-700">{score}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${riskBarColor(score)}`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

// Readiness + Risk -> Adoption Decision -> Recommended Opportunities.
// This panel is the one place that shows all three at once, in that
// order, so the relationship between them is visible rather than
// implied.
function AdoptionPanel({
  adoption,
  loading,
  error,
}: {
  adoption: SystemAdoption | null;
  loading: boolean;
  error: string | null;
}) {
  if (loading) {
    return <p className="text-sm text-slate-500">Loading…</p>;
  }

  if (error) {
    return <p className="text-sm text-red-600">{error}</p>;
  }

  if (!adoption) {
    return null;
  }

  const scored = adoption.opportunities.filter((o) => o.priority_score !== null);
  const unscored = adoption.opportunities.filter((o) => o.priority_score === null);

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <Badge label={adoption.decision} />
        <span className="text-sm text-slate-600">{adoption.reason}</span>
      </div>

      <p className="mb-3 text-xs font-medium text-slate-500">
        Recommended automation opportunities, best candidate first
      </p>

      {adoption.opportunities.length === 0 ? (
        <p className="text-sm text-slate-500">
          No recorded activities for this system yet.
        </p>
      ) : (
        <div className="space-y-2">
          {scored.map((opportunity, index) => (
            <OpportunityRow key={opportunity.id} rank={index + 1} opportunity={opportunity} />
          ))}
          {unscored.map((opportunity) => (
            <OpportunityRow key={opportunity.id} rank={null} opportunity={opportunity} />
          ))}
        </div>
      )}
    </div>
  );
}

function OpportunityRow({
  rank,
  opportunity,
}: {
  rank: number | null;
  opportunity: AutomationOpportunity;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-slate-100">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <span className="flex items-center gap-3">
          <span className="w-5 shrink-0 text-xs font-medium text-slate-400">
            {rank ?? "—"}
          </span>
          <span className="text-sm font-medium text-slate-900">{opportunity.activity}</span>
        </span>
        <span className="flex items-center gap-2">
          {opportunity.automation_potential && <Badge label={opportunity.automation_potential} />}
          <span className="text-slate-300">{expanded ? "▾" : "▸"}</span>
        </span>
      </button>

      {expanded && (
        <div className="border-t border-slate-100 px-4 py-3">
          <p className="mb-3 text-sm text-slate-600">{opportunity.description}</p>

          <p className="mb-3 text-sm text-slate-600">
            <span className="font-medium text-slate-900">AI opportunity:</span>{" "}
            {opportunity.ai_opportunity}
          </p>

          {opportunity.automation_potential && (
            <div className="mb-3 flex flex-wrap gap-x-6 gap-y-1.5 text-xs text-slate-500">
              <span>
                Automation potential <Badge label={opportunity.automation_potential} />
              </span>
              <span>
                Business impact <Badge label={opportunity.business_impact!} />
              </span>
              <span>
                Risk <Badge label={opportunity.automation_risk!} />
              </span>
              <span>
                Human oversight <Badge label={opportunity.human_oversight!} />
              </span>
            </div>
          )}

          <p className="text-sm text-slate-500">{opportunity.recommendation}</p>
        </div>
      )}
    </div>
  );
}

function BackLink() {
  return (
    <Link
      to="/systems"
      className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
    >
      <IconArrowRight className="h-3.5 w-3.5 rotate-180" />
      Back to Enterprise Systems
    </Link>
  );
}

function Row({ label, value, mono }: { label: string; value: ReactNode; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-4 text-sm">
      <dt className="shrink-0 text-slate-500">{label}</dt>
      <dd className={`text-right font-medium text-slate-900 ${mono ? "font-mono text-xs" : ""}`}>
        {value}
      </dd>
    </div>
  );
}
