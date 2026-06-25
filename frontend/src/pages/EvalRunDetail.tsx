import { useParams } from "react-router-dom";

export default function EvalRunDetail() {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Eval Run: {id}
      </h2>
      <p className="text-gray-500">
        Eval detail cards will be wired in Phase 6.
      </p>
    </div>
  );
}
