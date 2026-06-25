interface EvalResultCardProps {
  title: string;
  passed: boolean;
  score?: number;
  reasoning: string;
  details?: Record<string, unknown>;
  description?: string;
}

export default function EvalResultCard({
  title,
  passed,
  score,
  reasoning,
  details,
  description,
}: EvalResultCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <span
          className={`px-2 py-1 rounded text-sm font-medium ${
            passed
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {passed ? "PASS" : "FAIL"}
        </span>
      </div>
      {description && (
        <p className="text-xs text-gray-400 mb-3">{description}</p>
      )}
      {score !== undefined && (
        <div className="mb-2">
          <span className="text-2xl font-bold text-gray-900">
            {(score * 100).toFixed(1)}%
          </span>
          {title === "Quality" && (
            <span className="ml-2 text-xs text-gray-400">
              (pass: 70%+)
            </span>
          )}
          {title === "Hallucination" && (
            <span className="ml-2 text-xs text-gray-400">
              (pass: 30% or below)
            </span>
          )}
        </div>
      )}
      <p className="text-gray-600 text-sm whitespace-pre-wrap">{reasoning}</p>
      {details && Object.keys(details).length > 0 && (
        <details className="mt-4">
          <summary className="text-xs text-indigo-600 cursor-pointer hover:text-indigo-800">
            View raw details
          </summary>
          <pre className="mt-2 bg-gray-50 p-3 rounded text-xs overflow-auto">
            {JSON.stringify(details, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}
