// The Legacy-to-AI Adapter page.
//
// Flow: pick a source type -> pick which enterprise system's data to
// use (only sources of the chosen type are offered) -> "Run Adapter"
// -> see the result, one simple section at a time: numbers, then a
// clean records table (with an optional "what changed" expand per
// row, rather than dumping every before/after column at once), then
// the list of issues found.
//
// Every AdapterSource is already tied to one EnterpriseSystem (see
// backend/app/seed_data.py) -- "source type, then system" here is
// really just filtering the same list backend/app/routers/adapter.py
// returns from GET /adapter/sources, the same way EnterpriseSystems.tsx
// filters one fetched list instead of round-tripping per keystroke.

import { useEffect, useMemo, useState } from "react";
import Badge from "../components/Badge";
import Button from "../components/Button";
import Card from "../components/Card";
import MetricCard from "../components/MetricCard";
import PageHeader from "../components/PageHeader";
import { listAdapterSources, processSource } from "../api/adapter";
import { SOURCE_TYPES } from "../types";
import type {
  AdapterSource,
  DetectedIssue,
  ProcessingJobDetail,
  ProcessingResult,
  SourceType,
} from "../types";

// Which fields we show/compare in the records table -- kept short and
// plain-language on purpose so the table stays readable. Matches what
// backend/app/adapter/pipeline.py compares to decide "was this record
// cleaned" (minus `notes`, which isn't shown here).
const COMPARE_FIELDS: { key: string; label: string }[] = [
  { key: "city", label: "City" },
  { key: "phone", label: "Phone" },
  { key: "date_field", label: "Date" },
  { key: "country", label: "Country" },
];

export default function DataAdapter() {
  const [sources, setSources] = useState<AdapterSource[]>([]);
  const [loadingSources, setLoadingSources] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [sourceType, setSourceType] = useState<SourceType | "">("");
  const [selectedSourceId, setSelectedSourceId] = useState<number | "">("");

  const [job, setJob] = useState<ProcessingJobDetail | null>(null);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    listAdapterSources()
      .then((data) => {
        setSources(data);
        setLoadError(null);
      })
      .catch((err: Error) => setLoadError(err.message))
      .finally(() => setLoadingSources(false));
  }, []);

  const filteredSources = useMemo(
    () => (sourceType === "" ? sources : sources.filter((s) => s.source_type === sourceType)),
    [sources, sourceType],
  );

  function handleSourceTypeChange(value: SourceType | "") {
    setSourceType(value);
    // The system dropdown's options are about to change -- whatever
    // was picked before might not be in the new list, so clear it
    // rather than silently keeping a selection the user can't see.
    setSelectedSourceId("");
    setJob(null);
  }

  function handleRun() {
    if (selectedSourceId === "") return;
    setRunning(true);
    setRunError(null);
    processSource(selectedSourceId)
      .then((result) => setJob(result))
      .catch((err: Error) => setRunError(err.message))
      .finally(() => setRunning(false));
  }

  return (
    <div>
      <PageHeader
        title="Legacy-to-AI Adapter"
        description="Pick one system's raw data below and run it through the adapter to see it get cleaned, checked, and labeled."
      />

      <Card title="Step 1 — choose data">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">Source type</label>
            <select
              value={sourceType}
              onChange={(e) => handleSourceTypeChange(e.target.value as SourceType | "")}
              className="input w-auto"
            >
              <option value="">All source types</option>
              {SOURCE_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">
              Enterprise system
            </label>
            <select
              value={selectedSourceId}
              onChange={(e) => {
                setSelectedSourceId(e.target.value === "" ? "" : Number(e.target.value));
                setJob(null);
              }}
              className="input w-auto"
              disabled={filteredSources.length === 0}
            >
              <option value="">Select a system…</option>
              {filteredSources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.system_name} ({s.source_type})
                </option>
              ))}
            </select>
          </div>

          <Button onClick={handleRun} disabled={selectedSourceId === "" || running}>
            {running ? "Running…" : "Run Adapter"}
          </Button>
        </div>

        {loadingSources && (
          <p className="mt-4 text-sm text-slate-500">Loading data sources…</p>
        )}
        {loadError && (
          <p className="mt-4 text-sm text-red-600">
            Could not load data sources: {loadError} — is the backend running on port 8000?
          </p>
        )}
        {!loadingSources && !loadError && sources.length === 0 && (
          <p className="mt-4 text-sm text-slate-500">
            No data sources yet — add an Enterprise System first.
          </p>
        )}
        {runError && (
          <p className="mt-4 text-sm text-red-600">Could not run the adapter: {runError}</p>
        )}
      </Card>

      {job && (
        <div className="mt-6">
          <AdapterResult job={job} />
        </div>
      )}
    </div>
  );
}

function AdapterResult({ job }: { job: ProcessingJobDetail }) {
  const passed = job.ai_readiness_status === "Passed Basic Checks";

  return (
    <div className="space-y-6">
      <p className="text-xs font-medium text-slate-500">Step 2 — the result</p>

      <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
        <MetricCard label="Records processed" value={String(job.records_processed)} />
        <MetricCard label="Records cleaned" value={String(job.records_cleaned)} />
        <MetricCard label="Issues detected" value={String(job.issues_detected)} />
        <MetricCard
          label="Sensitive fields detected"
          value={String(job.sensitive_fields_detected)}
        />
      </div>

      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm font-medium text-slate-900">AI Readiness Status:</span>
          <span
            className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ${
              passed ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
            }`}
          >
            {job.ai_readiness_status}
          </span>
        </div>
        <p className="mt-1 text-xs text-slate-400">
          A basic pass/fail check, not the full AI Readiness Score — see that system's details
          page for its calculated score.
        </p>
      </Card>

      <Card title="Records by classification">
        <div className="flex flex-wrap gap-4">
          {Object.entries(job.classification_summary).map(([label, count]) => (
            <span key={label} className="flex items-center gap-2 text-sm text-slate-600">
              <Badge label={label} />
              {count} {count === 1 ? "record" : "records"}
            </span>
          ))}
        </div>
      </Card>

      <div>
        <h3 className="mb-1 text-sm font-semibold text-slate-900">Records</h3>
        <p className="mb-3 text-sm text-slate-500">
          Cleaned data. Click a row to see what the adapter actually changed.
        </p>
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-sm">
            <thead className="text-left text-xs font-medium text-slate-500">
              <tr>
                <th className="px-5 py-3">#</th>
                <th className="px-5 py-3">Name</th>
                <th className="px-5 py-3">City</th>
                <th className="px-5 py-3">Phone</th>
                <th className="px-5 py-3">Date</th>
                <th className="px-5 py-3">Classification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {job.results.map((r) => (
                <ResultRow key={r.id} result={r} />
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h3 className="mb-1 text-sm font-semibold text-slate-900">Issues found</h3>
        <p className="mb-3 text-sm text-slate-500">
          Everything the adapter flagged along the way — missing data, formatting problems,
          duplicates, and sensitive fields.
        </p>
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-sm">
            <thead className="text-left text-xs font-medium text-slate-500">
              <tr>
                <th className="px-5 py-3">Record</th>
                <th className="px-5 py-3">Type</th>
                <th className="px-5 py-3">Field</th>
                <th className="px-5 py-3">Description</th>
                <th className="px-5 py-3">Severity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {job.issues.map((issue) => (
                <IssueRow key={issue.id} issue={issue} />
              ))}
              {job.issues.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-slate-400">
                    No issues detected.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Records come from five different mock systems with different field
// names, and normalization can turn an empty/invalid value into
// something else -- so every lookup here has to tolerate a missing
// key instead of assuming one particular source's shape.
function cell(record: Record<string, unknown>, key: string): string {
  const value = record[key];
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function ResultRow({ result }: { result: ProcessingResult }) {
  const [expanded, setExpanded] = useState(false);

  // Only the fields that actually differ before vs. after -- this is
  // the whole point of the "click to see what changed" row: instead of
  // nine columns shown for every record whether or not anything
  // happened to it, you only see what's relevant to THIS record.
  const changes = COMPARE_FIELDS.filter(({ key }) => {
    const before = cell(result.raw_data, key);
    const after = cell(result.normalized_data, key);
    return before !== after;
  });

  return (
    <>
      <tr
        className={`cursor-pointer ${result.is_duplicate ? "bg-amber-50/60" : "hover:bg-slate-50"}`}
        onClick={() => setExpanded((v) => !v)}
      >
        <td className="px-5 py-3 text-slate-500">
          <span className="mr-1 inline-block w-3 text-slate-300">{expanded ? "▾" : "▸"}</span>
          {result.record_index + 1}
          {result.is_duplicate && (
            <span className="ml-1 text-amber-600" title="Duplicate record">
              ⚠
            </span>
          )}
        </td>
        <td className="px-5 py-3 font-medium text-slate-900">
          {cell(result.normalized_data, "full_name")}
        </td>
        <td className="px-5 py-3 text-slate-700">{cell(result.normalized_data, "city")}</td>
        <td className="px-5 py-3 text-slate-700">{cell(result.normalized_data, "phone")}</td>
        <td className="px-5 py-3 text-slate-700">{cell(result.normalized_data, "date_field")}</td>
        <td className="px-5 py-3">
          <Badge label={result.classification} />
        </td>
      </tr>
      {expanded && (
        <tr className="bg-slate-50/70">
          <td colSpan={6} className="px-5 py-3">
            {result.is_duplicate && (
              <p className="mb-1 text-xs text-amber-700">⚠ Flagged as a duplicate of another record.</p>
            )}
            {changes.length === 0 ? (
              <p className="text-xs text-slate-400">Nothing needed cleaning on this record.</p>
            ) : (
              <ul className="space-y-0.5 text-xs text-slate-600">
                {changes.map(({ key, label }) => (
                  <li key={key}>
                    <span className="font-medium">{label}:</span> {cell(result.raw_data, key)}{" "}
                    <span className="text-slate-400">→</span> {cell(result.normalized_data, key)}
                  </li>
                ))}
              </ul>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

function IssueRow({ issue }: { issue: DetectedIssue }) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-5 py-3 text-slate-500">
        {issue.record_index === null ? "—" : issue.record_index + 1}
      </td>
      <td className="px-5 py-3 text-slate-600">{issue.issue_type}</td>
      <td className="px-5 py-3 text-slate-600">{issue.field_name ?? "—"}</td>
      <td className="px-5 py-3">{issue.description}</td>
      <td className="px-5 py-3">
        <Badge label={issue.severity} />
      </td>
    </tr>
  );
}
