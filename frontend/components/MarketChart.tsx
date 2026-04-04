"use client";

import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type CandlePayload = {
  s?: string;
  t?: number[];
  c?: number[];
};

export function MarketChart({
  candles,
  requestedDays,
}: {
  candles: CandlePayload;
  requestedDays?: number;
}) {
  const t = candles.t ?? [];
  const c = candles.c ?? [];

  if (candles.s !== "ok" || t.length === 0 || c.length === 0) {
    return (
      <p className="text-sm text-muted mt-2">No chart data for this range.</p>
    );
  }

  const data = t.map((ts, i) => ({
    label: new Date(ts * 1000).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    }),
    close: c[i],
  }));

  const n = t.length;
  const spanNote =
    requestedDays != null
      ? `Close · daily · ${n} session${n === 1 ? "" : "s"} (requested ≤${requestedDays})`
      : `Close · daily · ${n} session${n === 1 ? "" : "s"}`;

  return (
    <div className="mt-4 w-full min-w-0">
      <p className="text-[10px] text-muted mb-2">{spanNote}</p>
      <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <XAxis
            dataKey="label"
            tick={{ fill: "#8b95a8", fontSize: 11 }}
            axisLine={{ stroke: "rgba(255,255,255,0.08)" }}
            tickLine={false}
          />
          <YAxis
            domain={["auto", "auto"]}
            tick={{ fill: "#8b95a8", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={56}
          />
          <Tooltip
            contentStyle={{
              background: "#151d2e",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            labelStyle={{ color: "#e8ecf2" }}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#5eead4"
            strokeWidth={1.5}
            dot={false}
            activeDot={{ r: 3, fill: "#5eead4" }}
          />
        </LineChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}
