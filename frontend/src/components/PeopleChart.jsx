import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function PeopleChart({ data }) {
  if (!data?.length) {
    return <p className="text-gray-500 text-sm">No timeline data available.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: -10, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
        <XAxis
          dataKey="time"
          tickFormatter={(v) => `${v}s`}
          stroke="#4b5563"
          tick={{ fill: "#9ca3af", fontSize: 11 }}
        />
        <YAxis
          allowDecimals={false}
          stroke="#4b5563"
          tick={{ fill: "#9ca3af", fontSize: 11 }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#111827",
            border: "1px solid #374151",
            borderRadius: "8px",
            fontSize: 13,
          }}
          labelFormatter={(v) => `Time: ${v}s`}
          formatter={(v) => [v, "People"]}
        />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "#60a5fa" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
