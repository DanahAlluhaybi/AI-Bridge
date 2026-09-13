// The AI Passport (Phase 8): a read-only, one-screen summary of a
// single use case -- what's being proposed, the system it touches, and
// the Readiness/Risk/Adoption picture behind the decision that was
// actually recorded for it at proposal time. Meant to be what an
// approver or auditor opens instead of piecing the story together
// across three different pages.

import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import Badge from "../components/Badge";
import Card from "../components/Card";
import PageHeader from "../components/PageHeader";
import { getAIPassport } from "../api/use-cases";
import type { AIPassport as AIPassportType } from "../types";

export default function AIPassport() {
  const { id } = useParams<{ id: string }>();
  const [passport, setPassport] = useState<AIPassportType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getAIPassport(Number(id))
      .then(setPassport)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div>
      <PageHeader
        title="AI Passport"
        description="A read-only summary of what was decided for one use case, and why."
      />

      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && (
        <p className="text-sm text-red-600">
          Could not load this AI Passport: {error}
        </p>
      )}

      {passport && (
        <div className="space-y-6">
          <Card title={passport.use_case_name} description={passport.purpose}>
            <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
              <Field label="Owner" value={passport.owner} />
              <Field
                label="System"
                value={
                  <Link
                    to={`/systems/${passport.system_id}`}
                    className="font-medium text-indigo-600 hover:text-indigo-700"
                  >
                    {passport.system_name}
                  </Link>
                }
              />
              <Field label="Requested automation" value={passport.requested_automation_level} />
              <Field
                label="Data classification"
                value={<Badge label={passport.data_classification} />}
              />
              <Field label="Security level" value={<Badge label={passport.security_level} />} />
              <Field label="Use case status" value={<Badge label={passport.use_case_status} />} />
            </div>
          </Card>

          <Card title="Readiness, Risk & Adoption at time of decision">
            <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
              <Field
                label="Readiness score"
                value={
                  passport.readiness_score === null ? "—" : `${passport.readiness_score} / 100`
                }
              />
              <Field
                label="Risk level"
                value={passport.risk_level === null ? "—" : <Badge label={passport.risk_level} />}
              />
              <Field label="AI Adoption decision" value={<Badge label={passport.adoption_decision} />} />
            </div>
          </Card>

          <Card title="Governance policy decision">
            <div className="mb-3 flex items-center gap-3">
              <Badge label={passport.policy_decision} />
              <span className="text-sm text-slate-600">{passport.policy_reason}</span>
            </div>
            <p className="text-xs text-slate-400">
              Proposed {new Date(passport.use_case_created_at).toLocaleString()} — Passport
              generated {new Date(passport.generated_at).toLocaleString()}
            </p>
          </Card>
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-1 text-sm text-slate-900">{value}</p>
    </div>
  );
}
