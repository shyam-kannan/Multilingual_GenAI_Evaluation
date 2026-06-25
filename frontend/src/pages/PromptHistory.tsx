import { useParams } from "react-router-dom";

export default function PromptHistory() {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Prompt History: {id}
      </h2>
      <p className="text-gray-500">
        Version history and charts will be wired in Phase 6.
      </p>
    </div>
  );
}
