import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { endpoints, type PromptHistoryData } from "../api/client";
import type { Prompt } from "../types";
import ScoreChart from "../components/ScoreChart";
import VersionDiffModal from "../components/VersionDiffModal";

export default function PromptHistory() {
  const { id } = useParams<{ id: string }>();
  const [prompt, setPrompt] = useState<Prompt | null>(null);
  const [history, setHistory] = useState<PromptHistoryData | null>(null);
  const [diffModal, setDiffModal] = useState<{
    open: boolean;
    diff: string;
    v1: string;
    v2: string;
  }>({ open: false, diff: "", v1: "", v2: "" });
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    endpoints
      .getPromptDetail(id)
      .then(setPrompt)
      .catch(() => setError("Failed to load prompt"));
    endpoints
      .getPromptHistory(id)
      .then(setHistory)
      .catch(() => {});
  }, [id]);

  if (error) return <p className="text-red-600 py-8">{error}</p>;
  if (!prompt) return <p className="text-gray-500 py-8">Loading...</p>;

  const chartData =
    history?.history.map((h) => {
      const row: Record<string, unknown> = { version: `v${h.version}` };
      for (const [locale, scores] of Object.entries(h.locale_scores)) {
        row[locale] = scores.avg_quality;
      }
      return row;
    }) ?? [];

  const handleDiff = async (v1Id: string, v2Id: string) => {
    if (!id) return;
    try {
      const result = await endpoints.getDiff(id, v1Id, v2Id);
      setDiffModal({
        open: true,
        diff: result.diff || "No differences",
        v1: `v${result.v1_version}`,
        v2: `v${result.v2_version}`,
      });
    } catch {
      setDiffModal({ open: true, diff: "Failed to load diff", v1: "", v2: "" });
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">{prompt.name}</h2>
      <p className="text-gray-500 mb-6">
        {prompt.versions?.length ?? 0} version(s) &middot; Created{" "}
        {new Date(prompt.created_at).toLocaleDateString()}
      </p>

      {/* Score chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Quality Scores by Version
          </h3>
          <ScoreChart data={chartData} />
        </div>
      )}

      {/* Version list */}
      <h3 className="text-lg font-medium text-gray-900 mb-3">Versions</h3>
      <div className="space-y-4">
        {(prompt.versions ?? []).map((v, idx) => (
          <div
            key={v.id}
            className="bg-white rounded-lg shadow p-4 border-l-4"
            style={{
              borderLeftColor: v.is_active ? "#10B981" : "#E5E7EB",
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <span className="text-lg font-semibold text-gray-900">
                  v{v.version}
                </span>
                {v.is_active && (
                  <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded font-medium">
                    ACTIVE
                  </span>
                )}
                {v.labels.map((label) => (
                  <span
                    key={label}
                    className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded font-medium"
                  >
                    {label}
                  </span>
                ))}
              </div>
              <span className="text-sm text-gray-500">
                {new Date(v.created_at).toLocaleString()}
              </span>
            </div>
            <pre className="text-sm text-gray-700 bg-gray-50 p-3 rounded mb-3 whitespace-pre-wrap max-h-32 overflow-auto">
              {v.content}
            </pre>
            <div className="flex gap-2">
              {idx > 0 && (
                <button
                  onClick={() =>
                    handleDiff(prompt.versions![idx - 1].id, v.id)
                  }
                  className="text-sm text-indigo-600 hover:text-indigo-900"
                >
                  Diff with v{prompt.versions![idx - 1].version}
                </button>
              )}
            </div>

            {/* Locale scores for this version */}
            {history?.history.find((h) => h.version_id === v.id)
              ?.locale_scores && (
              <div className="mt-3 flex flex-wrap gap-4">
                {Object.entries(
                  history!.history.find((h) => h.version_id === v.id)!
                    .locale_scores
                ).map(([locale, scores]) => (
                  <div key={locale} className="text-xs text-gray-600">
                    <span className="font-medium">{locale}</span>: Q{" "}
                    {(scores.avg_quality * 100).toFixed(0)}% / H{" "}
                    {(scores.avg_hallucination * 100).toFixed(0)}% ({scores.run_count}{" "}
                    runs)
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <VersionDiffModal
        isOpen={diffModal.open}
        onClose={() => setDiffModal({ ...diffModal, open: false })}
        diff={diffModal.diff}
        v1Label={diffModal.v1}
        v2Label={diffModal.v2}
      />
    </div>
  );
}
