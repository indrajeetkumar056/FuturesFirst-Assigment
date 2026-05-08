"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Props = {
  title: string;
  data: Array<Record<string, unknown>>;
};

function guessKeys(row: Record<string, unknown>): { xKey: string; yKey: string } {
  const keys = Object.keys(row);
  const xKey =
    keys.find((k) => typeof row[k] === "string") ??
    keys.find((k) => k.toLowerCase().includes("title")) ??
    keys[0] ??
    "x";
  const yKey =
    keys.find((k) => typeof row[k] === "number") ??
    keys.find((k) => k.toLowerCase().includes("minutes")) ??
    keys.find((k) => k.toLowerCase().includes("engagement")) ??
    keys[1] ??
    "y";
  return { xKey, yKey };
}

export function BarChartCard({ title, data }: Props) {
  const sample = data?.[0] ?? {};
  const { xKey, yKey } = guessKeys(sample);

  return (
    <div className="rounded-2xl bg-zinc-900 p-4 ring-1 ring-white/10">
      <div className="text-sm font-medium text-zinc-200">{title}</div>
      <div className="mt-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey={xKey} stroke="rgba(255,255,255,0.6)" />
            <YAxis stroke="rgba(255,255,255,0.6)" />
            <Tooltip
              contentStyle={{
                background: "rgba(24,24,27,0.95)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 12,
              }}
              labelStyle={{ color: "rgba(255,255,255,0.85)" }}
              itemStyle={{ color: "rgba(255,255,255,0.85)" }}
            />
            <Bar dataKey={yKey} fill="rgba(99,102,241,0.75)" radius={[10, 10, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

