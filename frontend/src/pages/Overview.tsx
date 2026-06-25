import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { endpoints, type OverviewData } from "../api/client";
import type { Prompt } from "../types";
import LocaleBadge from "../components/LocaleBadge";

const LOCALES = ["en-US", "es-MX", "ar-SA", "ja-JP"];

const LOCALE_NAMES: Record<string, string> = {
  "en-US": "English (US)",
  "es-MX": "Spanish (Mexico)",
  "ar-SA": "Arabic (Saudi Arabia)",
  "ja-JP": "Japanese (Japan)",
};

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

  const totalPassed = data.recent_runs.filter((r) => r.overall_passed).length;
  const totalRecent = data.recent_runs.length;

  return (
    <div>
      {/* Hero / explanation section */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Evaluation Overview
        </h2>
        <p className="text-gray-600 max-w-3xl">
          This dashboard monitors how well your AI-generated outputs perform
          across <strong>4 languages</strong>. Every time a prompt is run
          through the gateway, the output is scored on{" "}
          <strong>quality</strong> (is the response helpful and complete?),{" "}
          <strong>hallucination</strong> (did the AI make things up?),{" "}
          <strong>moderation</strong> (is the content safe?), and{" "}
          <strong>world-readiness</strong> (is it properly localized for the
          target language and culture?). An output must pass all four checks to
          be considered successful.
        </p>
      </div>

      {/* Locale pass rates */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-1">
          Pass Rate by Language
        </h3>
        <p className="text-xs text-gray-400 mb-4">
          Percentage of evaluation runs that passed all four checks for each
          locale
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {LOCALES.map((locale) => {
            const stats = data.locale_stats[locale];
            const rate = stats?.pass_rate ?? 0;
            const total = stats?.total_runs ?? 0;
            return (
              <div key={locale} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <LocaleBadge locale={locale} passRate={-1} />
                  <span
                    className={`text-2xl font-bold ${
                      rate >= 0.7
                        ? "text-green-600"
                        : rate >= 0.5
                        ? "text-yellow-600"
                        : "text-red-600"
                    }`}
                  >
                    {(rate * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-gray-500">
                  {LOCALE_NAMES[locale]} - {total} runs
                </p>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      rate >= 0.7
                        ? "bg-green-500"
                        : rate >= 0.5
                        ? "bg-yellow-500"
                        : "bg-red-500"
                    }`}
                    style={{ width: `${rate * 100}%` }}
                  />
                </div>
                {stats && (
                  <div className="mt-2 flex justify-between text-xs text-gray-400">
                    <span>
                      Avg quality: {(stats.avg_quality * 100).toFixed(0)}%
                    </span>
                    <span>
                      Avg halluc: {(stats.avg_hallucination * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Total Evaluation Runs</p>
          <p className="text-3xl font-bold text-gray-900">{data.total_runs}</p>
          <p className="text-xs text-gray-400 mt-1">
            Each run scores one AI output across all four checks
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Registered Prompts</p>
          <p className="text-3xl font-bold text-gray-900">
            {data.total_prompts}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Prompt templates being tracked and versioned
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Recent Pass Rate</p>
          <p className="text-3xl font-bold text-gray-900">
            {totalRecent > 0
              ? `${((totalPassed / totalRecent) * 100).toFixed(0)}%`
              : "N/A"}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {totalPassed} of {totalRecent} recent runs passed all checks
          </p>
        </div>
      </div>

      {/* Prompt list */}
      {prompts.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-medium text-gray-900 mb-1">Prompts</h3>
          <p className="text-sm text-gray-500 mb-3">
            Each prompt is a reusable template that can have multiple versions.
            Click "View History" to see how quality has changed across versions
            and languages.
          </p>
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
                  <tr key={p.id} className="hover:bg-gray-50">
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
                        View History &rarr;
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
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">
          Recent Evaluation Runs
        </h3>
        <p className="text-sm text-gray-500 mb-3">
          Each row is one evaluation of an AI output. Click an ID to see the
          full breakdown of what the AI generated and why it passed or failed.
        </p>
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
                    Language
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    <span title="How helpful, complete, and coherent the response is (higher is better, pass: 70%+)">
                      Quality
                    </span>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    <span title="How much the AI fabricated or made up (lower is better, pass: 30% or below)">
                      Hallucination
                    </span>
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
                      <span
                        className={
                          run.quality_score >= 0.7
                            ? "text-green-700"
                            : "text-red-600 font-medium"
                        }
                      >
                        {(run.quality_score * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <span
                        className={
                          run.hallucination_score <= 0.3
                            ? "text-green-700"
                            : "text-red-600 font-medium"
                        }
                      >
                        {(run.hallucination_score * 100).toFixed(1)}%
                      </span>
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

      {/* Metric legend */}
      <div className="mt-8 bg-gray-100 rounded-lg p-5">
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          How scoring works
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-gray-600">
          <div>
            <p className="font-medium text-gray-800">Quality (0-100%)</p>
            <p>
              An LLM judge scores relevance, completeness, and coherence.
              Must be 70% or higher to pass.
            </p>
          </div>
          <div>
            <p className="font-medium text-gray-800">Hallucination (0-100%)</p>
            <p>
              Measures how much the AI fabricated information not supported by
              the input. Must be 30% or lower to pass.
            </p>
          </div>
          <div>
            <p className="font-medium text-gray-800">Moderation</p>
            <p>
              Checks for harmful, unsafe, or inappropriate content. Uses a
              separate AI model and fails closed (errors count as failures).
            </p>
          </div>
          <div>
            <p className="font-medium text-gray-800">World-Readiness</p>
            <p>
              Validates the output uses the correct script and formatting for
              the target language (e.g., Arabic script for ar-SA, CJK for
              ja-JP).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
