import type { CIRun } from "../types";

interface CIRunRowProps {
  run: CIRun;
}

export default function CIRunRow({ run }: CIRunRowProps) {
  return (
    <tr className="border-b">
      <td className="py-3 px-4 text-sm text-gray-900">
        {run.id.slice(0, 8)}
      </td>
      <td className="py-3 px-4">
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
      <td className="py-3 px-4 text-sm text-gray-500">
        {run.regressions.length} regression(s)
      </td>
      <td className="py-3 px-4 text-sm text-gray-500">
        {new Date(run.created_at).toLocaleString()}
      </td>
    </tr>
  );
}
