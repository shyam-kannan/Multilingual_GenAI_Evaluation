interface LocaleBadgeProps {
  locale: string;
  passRate: number;
}

const LOCALE_META: Record<string, { color: string; label: string }> = {
  "en-US": { color: "bg-blue-100 text-blue-800", label: "English (US)" },
  "es-MX": { color: "bg-green-100 text-green-800", label: "Spanish (MX)" },
  "ar-SA": { color: "bg-purple-100 text-purple-800", label: "Arabic (SA)" },
  "ja-JP": { color: "bg-red-100 text-red-800", label: "Japanese (JP)" },
};

export default function LocaleBadge({ locale, passRate }: LocaleBadgeProps) {
  const meta = LOCALE_META[locale] ?? { color: "bg-gray-100 text-gray-800", label: locale };
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${meta.color}`}
      title={meta.label}
    >
      {passRate >= 0 ? `${locale}: ${(passRate * 100).toFixed(0)}%` : locale}
    </span>
  );
}
