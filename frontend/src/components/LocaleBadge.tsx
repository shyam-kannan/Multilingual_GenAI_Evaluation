interface LocaleBadgeProps {
  locale: string;
  passRate: number;
}

const localeColors: Record<string, string> = {
  "en-US": "bg-blue-100 text-blue-800",
  "es-MX": "bg-green-100 text-green-800",
  "ar-SA": "bg-purple-100 text-purple-800",
  "ja-JP": "bg-red-100 text-red-800",
};

export default function LocaleBadge({ locale, passRate }: LocaleBadgeProps) {
  const color = localeColors[locale] ?? "bg-gray-100 text-gray-800";
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${color}`}
    >
      {passRate >= 0 ? `${locale}: ${(passRate * 100).toFixed(0)}%` : locale}
    </span>
  );
}
