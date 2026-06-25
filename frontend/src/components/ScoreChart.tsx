import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";

interface ScoreChartProps {
  data: Array<Record<string, unknown>>;
  type?: "quality" | "hallucination";
}

const LOCALE_COLORS: Record<string, string> = {
  "en-US": "#3B82F6",
  "es-MX": "#10B981",
  "ar-SA": "#8B5CF6",
  "ja-JP": "#EF4444",
};

export default function ScoreChart({ data, type = "quality" }: ScoreChartProps) {
  const threshold = type === "quality" ? 0.7 : 0.3;
  const thresholdLabel = type === "quality" ? "Pass threshold (70%)" : "Fail threshold (30%)";

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} barCategoryGap="20%">
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="version" tick={{ fontSize: 13 }} />
        <YAxis
          domain={[0, 1]}
          tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
        />
        <Legend />
        <ReferenceLine
          y={threshold}
          stroke="#F59E0B"
          strokeDasharray="6 4"
          strokeWidth={2}
          label={{
            value: thresholdLabel,
            position: "insideTopRight",
            fill: "#92400E",
            fontSize: 11,
          }}
        />
        {Object.keys(LOCALE_COLORS).map((locale) => (
          <Bar
            key={locale}
            dataKey={locale}
            fill={LOCALE_COLORS[locale]}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
