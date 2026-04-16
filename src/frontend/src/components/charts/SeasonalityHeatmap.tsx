"use client";

import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { useTheme } from "next-themes";
import { MONTH_LABELS } from "@/lib/constants";
import type { SeasonalityRow } from "@/types/api";

interface Props {
  data: SeasonalityRow[];
  height?: number;
}

function returnColor(value: number | null): string {
  if (value == null) return "hsl(var(--muted))";
  if (value > 0) {
    const t = Math.min(1, Math.abs(value) / 5);
    return `rgba(34, 197, 94, ${0.2 + t * 0.7})`;
  }
  const t = Math.min(1, Math.abs(value) / 5);
  return `rgba(239, 68, 68, ${0.2 + t * 0.7})`;
}

function textReturn(value: number | null): string {
  if (value == null) return "hsl(var(--muted-foreground))";
  return value >= 0 ? "#166534" : "#991b1b";
}

export function SeasonalityHeatmap({ data, height = 420 }: Props) {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";

  const { years, avgData } = useMemo(() => {
    const years = data.map((r) => String(r.year));
    const avgData = MONTH_LABELS.map((month, mi) => {
      const vals = data
        .map((r) => r[(mi + 1) as keyof SeasonalityRow] as number | undefined)
        .filter((v): v is number => v != null);
      return {
        month,
        avg: vals.length
          ? parseFloat((vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1))
          : 0,
      };
    });
    return { years, avgData };
  }, [data]);

  const barOption = useMemo(() => {
    const text = dark ? "#64748b" : "#94a3b8";
    const gridLine = dark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)";
    return {
      backgroundColor: "transparent",
      animation: false,
      tooltip: {
        trigger: "axis",
        backgroundColor: dark ? "#1e293b" : "#fff",
        borderColor: dark ? "#334155" : "#e2e8f0",
        borderRadius: 8,
        textStyle: { color: dark ? "#f1f5f9" : "#0f172a", fontSize: 11 },
        formatter: (p: { name: string; value: number }[]) =>
          `${p[0]?.name}: <b>${p[0]?.value}%</b>`,
      },
      grid: { left: 40, right: 12, top: 8, bottom: 28 },
      xAxis: {
        type: "category",
        data: MONTH_LABELS,
        axisLabel: { color: text, fontSize: 9 },
        axisLine: { lineStyle: { color: gridLine } },
        splitLine: { show: false },
      },
      yAxis: {
        axisLabel: { color: text, fontSize: 9, formatter: (v: number) => `${v}%` },
        splitLine: { lineStyle: { color: gridLine } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: "bar",
          data: avgData.map((d) => ({
            value: d.avg,
            itemStyle: { color: d.avg >= 0 ? "#22c55e" : "#ef4444", borderRadius: [3, 3, 0, 0] },
          })),
          barMaxWidth: 28,
        },
      ],
    };
  }, [avgData, dark]);

  const gridHeight = Math.max(0, height - 120);
  const cellH = years.length > 0 ? Math.floor(gridHeight / years.length) : 24;

  return (
    <div style={{ width: "100%" }}>
      {/* Month header */}
      <div style={{ display: "grid", gridTemplateColumns: `40px repeat(12, 1fr)`, gap: 1, marginBottom: 1 }}>
        <div />
        {MONTH_LABELS.map((m) => (
          <div key={m} style={{ textAlign: "center", fontSize: 9, fontWeight: 600, color: "hsl(var(--muted-foreground))", padding: "2px 0" }}>
            {m}
          </div>
        ))}
      </div>

      {/* Heatmap grid */}
      <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
        {data.map((row, ri) => (
          <div key={years[ri]} style={{ display: "grid", gridTemplateColumns: `40px repeat(12, 1fr)`, gap: 1 }}>
            <div style={{ fontSize: 9, fontWeight: 600, color: "hsl(var(--muted-foreground))", display: "flex", alignItems: "center", justifyContent: "flex-end", paddingRight: 4, height: Math.max(20, cellH) }}>
              {years[ri]}
            </div>
            {Array.from({ length: 12 }, (_, mi) => {
              const val = row[(mi + 1) as keyof SeasonalityRow] as number | undefined;
              const v = val != null ? parseFloat(val.toFixed(1)) : null;
              return (
                <div key={mi} title={`${MONTH_LABELS[mi]} ${years[ri]}: ${v != null ? `${v}%` : "N/A"}`}
                  style={{ height: Math.max(20, cellH), background: returnColor(v), color: textReturn(v), display: "flex", alignItems: "center", justifyContent: "center", fontSize: 8, fontWeight: 500, borderRadius: 2, cursor: "default" }}>
                  {v != null ? `${v}%` : ""}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {/* Average bar chart */}
      <div style={{ marginTop: 8 }}>
        <ReactECharts option={barOption} style={{ height: 100, width: "100%" }} notMerge />
      </div>
    </div>
  );
}
