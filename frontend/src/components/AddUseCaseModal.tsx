// The "Propose Use Case" form, shown as a modal overlay on the AI Use
// Cases page. Same controlled-form pattern as AddSystemModal.tsx.
// Submitting runs the use case through the governance policy
// immediately -- the caller (AIUseCases.tsx) reloads the list right
// after, so the newly proposed use case shows up with whatever
// decision it actually got.

import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { listSystems } from "../api/systems";
import { createUseCase } from "../api/use-cases";
import Button from "./Button";
import type { AIUseCaseInput, EnterpriseSystem } from "../types";
import { AUTOMATION_LEVELS } from "../types";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

const EMPTY_FORM: AIUseCaseInput = {
  system_id: 0,
  name: "",
  purpose: "",
  owner: "",
  requested_automation_level: "Assisted",
};

export default function AddUseCaseModal({ onClose, onCreated }: Props) {
  const [systems, setSystems] = useState<EnterpriseSystem[]>([]);
  const [form, setForm] = useState<AIUseCaseInput>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSystems()
      .then((data) => {
        setSystems(data);
        if (data.length > 0) {
          setForm((f) => ({ ...f, system_id: data[0].id }));
        }
      })
      .catch(() => {
        // The form still renders -- the select just stays empty and
        // the submit button below explains why nothing can be chosen.
      });
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createUseCase(form);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to propose use case");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 px-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-6 shadow-popover">
        <h3 className="mb-4 text-base font-semibold text-slate-900">Propose AI Use Case</h3>

        {systems.length === 0 ? (
          <p className="text-sm text-slate-500">
            No enterprise systems yet — add one on the Enterprise Systems page before proposing a
            use case.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Field label="Enterprise system">
              <select
                value={form.system_id}
                onChange={(e) => setForm({ ...form, system_id: Number(e.target.value) })}
                className="input"
              >
                {systems.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Use case name">
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="input"
                placeholder="e.g. Invoice Duplicate Flagging"
              />
            </Field>

            <Field label="Purpose">
              <textarea
                required
                value={form.purpose}
                onChange={(e) => setForm({ ...form, purpose: e.target.value })}
                className="input min-h-20"
                placeholder="What is this use case for, in a sentence or two?"
              />
            </Field>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Owner">
                <input
                  required
                  value={form.owner}
                  onChange={(e) => setForm({ ...form, owner: e.target.value })}
                  className="input"
                  placeholder="e.g. Name — Role"
                />
              </Field>
              <Field label="Requested automation level">
                <select
                  value={form.requested_automation_level}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      requested_automation_level: e.target
                        .value as AIUseCaseInput["requested_automation_level"],
                    })
                  }
                  className="input"
                >
                  {AUTOMATION_LEVELS.map((level) => (
                    <option key={level} value={level}>
                      {level}
                    </option>
                  ))}
                </select>
              </Field>
            </div>

            <p className="text-xs text-slate-400">
              Advisory: AI only ever suggests, a human always acts. Assisted: AI acts with a human
              reviewing along the way. Full: AI acts on its own once approved.
            </p>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Submitting…" : "Submit for policy review"}
              </Button>
            </div>
          </form>
        )}

        {systems.length === 0 && (
          <div className="flex justify-end pt-4">
            <Button type="button" variant="ghost" onClick={onClose}>
              Close
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-500">{label}</span>
      {children}
    </label>
  );
}
