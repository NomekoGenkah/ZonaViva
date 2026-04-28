import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useApp } from "../contexts/AppContext";

export default function PeopleChart({ data }) {
  const { theme, t } = useApp();
  const dark = theme === "dark";

  if (!data?.length) {
    return <p className="text-gray-400 dark:text-gray-500 text-sm">{t("results.no_data")}</p>;
  }

  const grid = dark ? "#1f2937" : "#e5e7eb";
  const axis = dark ? "#4b5563" : "#9ca3af";
  const tick = dark ? "#9ca3af" : "#6b7280";
  const tooltipBg = dark ? "#111827" : "#ffffff";
  const tooltipBorder = dark ? "#374151" : "#e5e7eb";
  const tooltipColor = dark ? "#f3f4f6" : "#111827";

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: -10, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={grid} />
        <XAxis
          dataKey="time"
          tickFormatter={(v) => `${v}s`}
          stroke={axis}
          tick={{ fill: tick, fontSize: 11 }}
        />
        <YAxis
          allowDecimals={false}
          stroke={axis}
          tick={{ fill: tick, fontSize: 11 }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: tooltipBg,
            border: `1px solid ${tooltipBorder}`,
            borderRadius: "8px",
            fontSize: 13,
            color: tooltipColor,
          }}
          labelFormatter={(v) => `${t("results.time_label")}: ${v}s`}
          formatter={(v) => [v, t("results.people_label")]}
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
