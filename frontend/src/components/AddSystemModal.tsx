// The "Add System" form, shown as a modal overlay on top of the
// Enterprise Systems page. It's a controlled form: every input's value
// lives in React state (`form`), and every keystroke updates that
// state -- this is the standard React pattern, and it's what lets us
// validate and submit the whole form as one JavaScript object.

import { useState, type FormEvent, type ReactNode } from "react";
import { createSystem } from "../api/systems";
import type { EnterpriseSystemInput } from "../types";
import {
  DATA_CLASSIFICATIONS,
  INTEGRATION_TYPES,
  SECURITY_LEVELS,
  SYSTEM_STATUSES,
  SYSTEM_TYPES,
} from "../types";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

const EMPTY_FORM: EnterpriseSystemInput = {
  name: "",
  system_type: "ERP",
  department: "",
  owner: "",
  integration_type: "REST API",
  data_types: [],
  data_classification: "Internal",
  security_level: "Medium",
  status: "Pending",
  data_source: "",
};

export default function AddSystemModal({ onClose, onCreated }: Props) {
  const [form, setForm] = useState<EnterpriseSystemInput>(EMPTY_FORM);
  // data_types is a list on the backend, but a comma-separated text
  // field is a much simpler UI than "add tag" buttons for an MVP -- we
  // split it into an array right before submitting.
  const [dataTypesText, setDataTypesText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const data_types = dataTypesText
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      await createSystem({ ...form, data_types });
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create system");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
        <h3 className="mb-4 text-lg font-medium">Add Enterprise System</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field label="System name">
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="input"
              placeholder="e.g. Regional Sales Database"
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="System type">
              <select
                value={form.system_type}
                onChange={(e) =>
                  setForm({
                    ...form,
                    system_type: e.target.value as EnterpriseSystemInput["system_type"],
                  })
                }
                className="input"
              >
                {SYSTEM_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Integration type">
              <select
                value={form.integration_type}
                onChange={(e) =>
                  setForm({
                    ...form,
                    integration_type: e.target
                      .value as EnterpriseSystemInput["integration_type"],
                  })
                }
                className="input"
              >
                {INTEGRATION_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Department">
              <input
                required
                value={form.department}
                onChange={(e) => setForm({ ...form, department: e.target.value })}
                className="input"
                placeholder="e.g. Finance"
              />
            </Field>
            <Field label="Owner">
              <input
                required
                value={form.owner}
                onChange={(e) => setForm({ ...form, owner: e.target.value })}
                className="input"
                placeholder="e.g. Name — Role"
              />
            </Field>
          </div>

          <Field label="Data types (comma-separated)">
            <input
              value={dataTypesText}
              onChange={(e) => setDataTypesText(e.target.value)}
              className="input"
              placeholder="e.g. Employee Records, Payroll"
            />
          </Field>

          <div className="grid grid-cols-3 gap-4">
            <Field label="Data classification">
              <select
                value={form.data_classification}
                onChange={(e) =>
                  setForm({
                    ...form,
                    data_classification: e.target
                      .value as EnterpriseSystemInput["data_classification"],
                  })
                }
                className="input"
              >
                {DATA_CLASSIFICATIONS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Security level">
              <select
                value={form.security_level}
                onChange={(e) =>
                  setForm({
                    ...form,
                    security_level: e.target
                      .value as EnterpriseSystemInput["security_level"],
                  })
                }
                className="input"
              >
                {SECURITY_LEVELS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Status">
              <select
                value={form.status}
                onChange={(e) =>
                  setForm({
                    ...form,
                    status: e.target.value as EnterpriseSystemInput["status"],
                  })
                }
                className="input"
              >
                {SYSTEM_STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <Field label="Data source (optional — a mock endpoint or file path)">
            <input
              value={form.data_source}
              onChange={(e) => setForm({ ...form, data_source: e.target.value })}
              className="input"
              placeholder="e.g. https://internal.mock/api/v1"
            />
          </Field>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {submitting ? "Creating…" : "Create System"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-500">
        {label}
      </span>
      {children}
    </label>
  );
}
