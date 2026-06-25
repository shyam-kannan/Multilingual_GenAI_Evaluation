import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { endpoints, type OverviewData } from "../api/client";
import type { Prompt } from "../types";
import LocaleBadge from "../components/LocaleBadge";

const LOCALES = ["en-US", "es-MX", "ar-SA", "ja-JP"];

export default function Overview() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    endpoints
      .getOverview()
      .then(setData)
      .catch(() => setError("Failed to load overview data"));
    endpoints
      .getPrompts()
      .then(setPrompts)
      .catch(() => {});
  }, []);

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <p className="text-gray-500 mt-2">Make sure the backend is running.</p>
      </div>
    );
  }

  if (!data) {
    return <p className="text-gray-500 py-8">Loading...</p>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Evaluation Overview
      </h2>

      {/* Locale badges */}
      <div className="flex flex-wrap gap-3 mb-8">
        {LOCALES.map((locale) => (
          <LocaleBadge
            key={locale}
            locale={locale}
            passRate={data.locale_stats[locale]?.pass_rate ?? 0}
          />
        ))}
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Total Eval Runs</p>
          <p className="text-3xl font-bold text-gray-900">{data.total_runs}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Registered Prompts</p>
          <p className="text-3xl font-bold text-gray-900">
            {data.total_prompts}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Overall Pass Rate</p>
          <p className="text-3xl font-bold text-gray-900">
            {data.total_runs > 0
              ? `${(
                  (data.recent_runs.filter((r) => r.overall_passed).length /
                    Math.min(data.recent_runs.length, 10)) *
                  100
                ).toFixed(0)}%`
              : "N/A"}
          </p>
        </div>
      </div>

      {/* Prompt list */}
      {prompts.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-3">Prompts</h3>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Created
                  </th>
                  <th className="px-6 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {prompts.map((p) => (
                  <tr key={p.id}>
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      {p.name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(p.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/prompts/${p.id}`}
                        className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                      >
                        View History
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recent eval runs */}
      <h3 className="text-lg font-medium text-gray-900 mb-3">
        Recent Eval Runs
      </h3>
      {data.recent_runs.length === 0 ? (
        <p className="text-gray-500">No eval runs yet.</p>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Locale
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Quality
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Hallucination
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Result
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.recent_runs.map((run) => (
                <tr key={run.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm">
                    <Link
                      to={`/eval/${run.id}`}
                      className="text-indigo-600 hover:text-indigo-900"
                    >
                      {run.id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td className="px-6 py-4">
                    <LocaleBadge locale={run.locale} passRate={-1} />
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {(run.quality_score * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {(run.hallucination_score * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        run.overall_passed
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {run.overall_passed ? "PASS" : "FAIL"}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(run.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
