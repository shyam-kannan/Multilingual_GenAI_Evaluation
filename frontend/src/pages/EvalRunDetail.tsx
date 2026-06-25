import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { endpoints } from "../api/client";
import type { EvalRun } from "../types";
import EvalResultCard from "../components/EvalResultCard";
import LocaleBadge from "../components/LocaleBadge";

export default function EvalRunDetail() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<EvalRun | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    endpoints
      .getEvalRun(id)
      .then(setRun)
      .catch(() => setError("Failed to load eval run"));
  }, [id]);

  if (error) return <p className="text-red-600 py-8">{error}</p>;
  if (!run) return <p className="text-gray-500 py-8">Loading...</p>;

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Eval Run Detail</h2>
        <LocaleBadge locale={run.locale} passRate={-1} />
        <span
          className={`px-3 py-1 rounded text-sm font-medium ${
            run.overall_passed
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {run.overall_passed ? "OVERALL PASS" : "OVERALL FAIL"}
        </span>
      </div>

      <div className="text-sm text-gray-500 mb-6">
        ID: {run.id} &middot;{" "}
        {new Date(run.created_at).toLocaleString()}
      </div>

      {/* Input/Output */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Input</h3>
          <p className="text-gray-900 whitespace-pre-wrap">{run.input_text}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            LLM Output
          </h3>
          <p className="text-gray-900 whitespace-pre-wrap" dir="auto">
            {run.llm_output}
          </p>
        </div>
      </div>

      {/* Score cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <EvalResultCard
          title="Quality"
          passed={run.quality_score >= 0.7}
          score={run.quality_score}
          reasoning={run.quality_reasoning}
        />
        <EvalResultCard
          title="Hallucination"
          passed={run.hallucination_score <= 0.3}
          score={run.hallucination_score}
          reasoning={run.hallucination_reasoning}
        />
        <EvalResultCard
          title="Moderation"
          passed={run.moderation_passed}
          reasoning={run.moderation_reasoning}
        />
        <EvalResultCard
          title="World Readiness"
          passed={run.world_readiness_passed}
          reasoning={
            run.world_readiness_details?.checks
              ? (run.world_readiness_details.checks as { check: string; passed: boolean; detail: string }[])
                  .map(
                    (c: { check: string; passed: boolean; detail: string }) =>
                      `${c.passed ? "PASS" : "FAIL"} ${c.check}: ${c.detail}`
                  )
                  .join("\n")
              : "No details available"
          }
          details={run.world_readiness_details}
        />
      </div>
    </div>
  );
}
