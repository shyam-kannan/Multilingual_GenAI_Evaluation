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
      <h2 className="text-2xl font-bold text-gray-900 mb-6">CI History</h2>

      {runs.length === 0 ? (
        <p className="text-gray-500">No CI runs yet.</p>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Run ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Regressions
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Baseline
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {runs.map((run) => (
                <>
                  <tr key={run.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900 font-mono">
                      {run.id.slice(0, 8)}...
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          run.status === "passed"
                            ? "bg-green-100 text-green-800"
                            : run.status === "failed"
                            ? "bg-red-100 text-red-800"
                            : "bg-yellow-100 text-yellow-800"
                        }`}
                      >
                        {run.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {run.regressions.length} regression(s)
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {run.baseline_version_id
                        ? run.baseline_version_id.slice(0, 8) + "..."
                        : "None"}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() =>
                          setExpanded(expanded === run.id ? null : run.id)
                        }
                        className="text-sm text-indigo-600 hover:text-indigo-900"
                      >
                        {expanded === run.id ? "Hide" : "Details"}
                      </button>
                    </td>
                  </tr>
                  {expanded === run.id && (
                    <tr key={`${run.id}-detail`}>
                      <td colSpan={6} className="px-6 py-4 bg-gray-50">
                        {run.regressions.length > 0 && (
                          <div className="mb-4">
                            <h4 className="text-sm font-medium text-red-700 mb-2">
                              Regressions
                            </h4>
                            <div className="space-y-2">
                              {run.regressions.map((reg, i) => (
                                <div
                                  key={i}
                                  className="flex items-center gap-4 text-sm"
                                >
                                  <span className="font-medium text-gray-900">
                                    {reg.locale}
                                  </span>
                                  <span className="text-gray-600">
                                    {reg.metric}
                                  </span>
                                  <span className="text-gray-500">
                                    baseline: {(reg.baseline * 100).toFixed(1)}%
                                  </span>
                                  <span className="text-gray-500">
                                    candidate:{" "}
                                    {(reg.candidate * 100).toFixed(1)}%
                                  </span>
                                  <span className="text-red-600 font-medium">
                                    delta: {(reg.delta * 100).toFixed(1)}%
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        <h4 className="text-sm font-medium text-gray-700 mb-2">
                          Locale Details
                        </h4>
                        <pre className="text-xs bg-white p-3 rounded border overflow-auto">
                          {JSON.stringify(run.details, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
