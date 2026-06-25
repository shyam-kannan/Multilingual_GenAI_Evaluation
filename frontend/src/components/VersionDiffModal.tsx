interface VersionDiffModalProps {
  isOpen: boolean;
  onClose: () => void;
  diff: string;
  v1Label: string;
  v2Label: string;
}

export default function VersionDiffModal({
  isOpen,
  onClose,
  diff,
  v1Label,
  v2Label,
}: VersionDiffModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[80vh] overflow-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-medium">
            Diff: {v1Label} vs {v2Label}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            Close
          </button>
        </div>
        <pre className="p-4 text-sm font-mono whitespace-pre-wrap">{diff}</pre>
      </div>
    </div>
  );
}
