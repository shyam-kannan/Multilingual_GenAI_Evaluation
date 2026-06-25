interface EvalResultCardProps {
  title: string;
  passed: boolean;
  score?: number;
  reasoning: string;
  details?: Record<string, unknown>;
}

export default function EvalResultCard({
  title,
  passed,
  score,
  reasoning,
  details,
}: EvalResultCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
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
      {score !== undefined && (
        <div className="mb-2 text-2xl font-bold text-gray-900">
          {(score * 100).toFixed(1)}%
        </div>
      )}
      <p className="text-gray-600 text-sm whitespace-pre-wrap">{reasoning}</p>
      {details && Object.keys(details).length > 0 && (
        <pre className="mt-4 bg-gray-50 p-3 rounded text-xs overflow-auto">
          {JSON.stringify(details, null, 2)}
        </pre>
      )}
    </div>
  );
}
