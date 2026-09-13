// The AI Playground (Phase 10): pick an Approved use case, send it a
// prompt, and see what the (free, deterministic) MockAIProvider sends
// back. Only Approved use cases show up in the picker -- the backend
// rejects a prompt for anything else, this just avoids offering the
// choice in the first place.

import { useEffect, useState } from "react";
import Button from "../components/Button";
import Card from "../components/Card";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { askPlayground, getPlaygroundHistory } from "../api/playground";
import { listUseCases } from "../api/use-cases";
import type { AIUseCase, PlaygroundRequest } from "../types";

export default function Playground() {
  const [useCases, setUseCases] = useState<AIUseCase[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [prompt, setPrompt] = useState("");
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<PlaygroundRequest[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  const approvedUseCases = useCases.filter((uc) => uc.status === "Approved");

  function loadHistory(useCaseId?: number) {
    setHistoryLoading(true);
    getPlaygroundHistory(useCaseId)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setHistoryLoading(false));
  }

  useEffect(() => {
    listUseCases()
      .then((data) => {
        setUseCases(data);
        const firstApproved = data.find((uc) => uc.status === "Approved");
        if (firstApproved) setSelectedId(firstApproved.id);
      })
      .catch((err: Error) => setError(err.message));
    loadHistory();
  }, []);

  async function handleAsk() {
    if (!selectedId || !prompt.trim()) return;
    setAsking(true);
    setError(null);
    try {
      await askPlayground({ use_case_id: selectedId, prompt: prompt.trim() });
      setPrompt("");
      loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run this prompt");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="AI Playground"
        description="Try an Approved use case out with a real prompt -- responses come from a free, deterministic mock model, not a paid API."
      />

      {approvedUseCases.length === 0 ? (
        <EmptyState
          title="No Approved use cases yet"
          description="Propose a use case and get it Approved (directly, or through the Approval Center) before it can be run here."
        />
      ) : (
        <Card className="mb-6">
          <div className="mb-4 space-y-3">
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">Use case</span>
              <select
                value={selectedId ?? ""}
                onChange={(e) => setSelectedId(Number(e.target.value))}
                className="input"
              >
                {approvedUseCases.map((uc) => (
                  <option key={uc.id} value={uc.id}>
                    {uc.name} — {uc.system_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">Prompt</span>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="input min-h-24"
                placeholder="Ask this use case something…"
              />
            </label>
          </div>

          {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

          <Button onClick={handleAsk} disabled={asking || !prompt.trim()}>
            {asking ? "Running…" : "Run prompt"}
          </Button>
        </Card>
      )}

      <h3 className="mb-3 text-sm font-semibold text-slate-900">History</h3>
      {historyLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {!historyLoading && history.length === 0 && (
        <EmptyState title="No prompts run yet" description="Run one above to see it show up here." />
      )}
      {!historyLoading && history.length > 0 && (
        <div className="space-y-4">
          {history.map((entry) => (
            <Card key={entry.id}>
              <div className="mb-2 flex items-center justify-between gap-3">
                <span className="text-sm font-medium text-slate-900">{entry.use_case_name}</span>
                <span className="text-xs text-slate-400">
                  {new Date(entry.created_at).toLocaleString()}
                </span>
              </div>
              <p className="mb-2 text-sm text-slate-900">
                <span className="font-medium">Prompt: </span>
                {entry.prompt}
              </p>
              <p className="text-sm text-slate-600">{entry.response}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
