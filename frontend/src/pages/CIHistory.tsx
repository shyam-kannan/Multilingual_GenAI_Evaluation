import { useEffect, useState } from "react";
import { endpoints, type CIHistoryEntry } from "../api/client";

export default function CIHistory() {
  const [runs, setRuns] = useState<CIHistoryEntry[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    endpoints
      .getCIHistory()
      .then(setRuns)
      .catch(() => setError("Failed to load CI history"));
  }, []);

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <p className="text-gray-500 mt-2">Make sure the backend is running.</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        CI Regression History
      </h2>
      <p className="text-sm text-gray-600 mb-6 max-w-3xl">
        Every time a new prompt version is tested, the CI gate compares it
        against the current production version using golden test examples. If
        the quality score drops by more than 10% or the hallucination score
        rises by more than 10% in any language, the check fails and the version
        is blocked from shipping. This prevents regressions from reaching
        production.
      </p>

      {runs.length === 0 ? (
        <p className="text-gray-500">No CI runs yet.</p>
      ) : (
        <div className="space-y-4">
          {runs.map((run) => (
            <div
              key={run.id}
              className={`bg-white rounded-lg shadow border-l-4 ${
                run.status === "passed"
                  ? "border-green-500"
                  : run.status === "failed"
                  ? "border-red-500"
                  : "border-yellow-500"
              }`}
            >
              <div className="p-5">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2.5 py-1 rounded text-xs font-bold uppercase ${
                        run.status === "passed"
                          ? "bg-green-100 text-green-800"
                          : run.status === "failed"
                          ? "bg-red-100 text-red-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {run.status}
                    </span>
                    <span className="text-sm text-gray-900 font-mono">
                      {run.id.slice(0, 12)}...
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {new Date(run.created_at).toLocaleString()}
                  </span>
                </div>

                <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-3">
                  <span>
                    <span className="text-gray-400">Candidate:</span>{" "}
                    <span className="font-mono">
                      {run.candidate_version_id.slice(0, 8)}...
                    </span>
                  </span>
                  <span>
                    <span className="text-gray-400">Baseline:</span>{" "}
                    {run.baseline_version_id ? (
                      <span className="font-mono">
                        {run.baseline_version_id.slice(0, 8)}...
                      </span>
                    ) : (
                      <span className="italic text-gray-400">
                        None (first version)
                      </span>
                    )}
                  </span>
                  <span>
                    <span className="text-gray-400">Regressions:</span>{" "}
                    <span
                      className={
                        run.regressions.length > 0
                          ? "text-red-600 font-medium"
                          : "text-green-600"
                      }
                    >
                      {run.regressions.length}
                    </span>
                  </span>
                </div>

                {/* Regressions inline */}
                {run.regressions.length > 0 && (
                  <div className="bg-red-50 rounded-lg p-4 mb-3">
                    <p className="text-xs font-medium text-red-800 uppercase tracking-wide mb-2">
                      Detected regressions
                    </p>
                    <div className="space-y-2">
                      {run.regressions.map((reg, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-3 text-sm"
                        >
                          <span className="font-medium text-gray-900 w-12">
                            {reg.locale}
                          </span>
                          <span className="text-gray-600 w-24">
                            {reg.metric}
                          </span>
                          <span className="text-gray-500">
                            baseline:{" "}
                            <span className="font-mono">
                              {(reg.baseline * 100).toFixed(1)}%
                            </span>
                          </span>
                          <span className="text-gray-300">&#8594;</span>
                          <span className="text-gray-500">
                            candidate:{" "}
                            <span className="font-mono">
                              {(reg.candidate * 100).toFixed(1)}%
                            </span>
                          </span>
                          <span className="text-red-600 font-bold">
                            {(reg.delta * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {run.status === "passed" && run.regressions.length === 0 && (
                  <p className="text-sm text-green-700">
                    {run.baseline_version_id
                      ? "No quality or hallucination regressions detected across any language."
                      : "First version for this prompt. No baseline to compare against, so the check passed automatically."}
                  </p>
                )}

                <button
                  onClick={() =>
                    setExpanded(expanded === run.id ? null : run.id)
                  }
                  className="text-sm text-indigo-600 hover:text-indigo-900 mt-2"
                >
                  {expanded === run.id
                    ? "Hide locale details"
                    : "Show locale details"}
                </button>

                {expanded === run.id && (
                  <div className="mt-3 bg-gray-50 rounded-lg p-4">
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                      Per-language scores for this CI run
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                      {Object.entries(
                        run.details as Record<
                          string,
                          {
                            quality: number;
                            hallucination: number;
                            run_count: number;
                          }
                        >
                      ).map(([locale, d]) => (
                        <div
                          key={locale}
                          className="bg-white rounded border p-3"
                        >
                          <p className="text-sm font-medium text-gray-900 mb-1">
                            {locale}
                          </p>
                          <div className="flex justify-between text-xs text-gray-600">
                            <span>
                              Quality:{" "}
                              <span
                                className={
                                  d.quality >= 0.7
                                    ? "text-green-700 font-medium"
                                    : "text-red-600 font-medium"
                                }
                              >
                                {(d.quality * 100).toFixed(0)}%
                              </span>
                            </span>
                            <span>
                              Halluc:{" "}
                              <span
                                className={
                                  d.hallucination <= 0.3
                                    ? "text-green-700 font-medium"
                                    : "text-red-600 font-medium"
                                }
                              >
                                {(d.hallucination * 100).toFixed(0)}%
                              </span>
                            </span>
                          </div>
                          <p className="text-xs text-gray-400 mt-1">
                            {d.run_count} eval runs
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="mt-8 bg-gray-100 rounded-lg p-5">
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          How CI regression detection works
        </h4>
        <div className="text-sm text-gray-600 space-y-2">
          <p>
            1. The system finds the current "production" version of the prompt
            as the baseline.
          </p>
          <p>
            2. It runs the candidate version against all golden test examples
            for each language.
          </p>
          <p>
            3. It compares the average quality and hallucination scores to the
            baseline.
          </p>
          <p>
            4. If quality drops by more than 10% or hallucination rises by
            more than 10% in any language, the CI check fails.
          </p>
        </div>
      </div>
    </div>
  );
}
