import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface ScoreChartProps {
  data: Array<Record<string, unknown>>;
}

export default function ScoreChart({ data }: ScoreChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="version" />
        <YAxis domain={[0, 1]} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="en-US" stroke="#3B82F6" />
        <Line type="monotone" dataKey="es-MX" stroke="#10B981" />
        <Line type="monotone" dataKey="ar-SA" stroke="#8B5CF6" />
        <Line type="monotone" dataKey="ja-JP" stroke="#EF4444" />
      </LineChart>
    </ResponsiveContainer>
  );
}
