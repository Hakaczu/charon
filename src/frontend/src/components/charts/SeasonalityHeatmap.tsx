"use client";

import ReactECharts from "echarts-for-react";
import { useTheme } from "next-themes";
import { useMemo } from "react";
import { MONTH_LABELS } from "@/lib/constants";
import type { SeasonalityRow } from "@/types/api";

interface Props {
  data: SeasonalityRow[];
  height?: number;
}

export function SeasonalityHeatmap({ data, height = 420 }: Props) {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";

  const option = useMemo(() => {
    const years = data.map((r) => String(r.year));
    const textColor = dark ? "#94a3b8" : "#64748b";

    const heatmapData: [number, number, number | null][] = [];
    data.forEach((row, yi) => {
      for (let m = 1; m <= 12; m++) {
        const val = row[m as keyof SeasonalityRow] as number | undefined;
        heatmapData.push([m - 1, yi, val != null ? parseFloat(val.toFixed(1)) : null]);
      }
    });

    // Average per month
    const avgData: (number | null)[] = Array.from({ length: 12 }, (_, mi) => {
      const vals = data.map((r) => r[(mi + 1) as keyof SeasonalityRow] as number | undefined).filter((v) => v != null) as number[];
      return vals.length ? parseFloat((vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1)) : null;
    });

    const allVals = heatmapData.map((d) => d[2]).filter((v): v is number => v != null);
    const maxAbs = Math.max(Math.abs(Math.min(...allVals)), Math.abs(Math.max(...allVals)), 1);

    return {
      backgroundColor: "transparent",
      tooltip: {
        formatter: (p: { data: [number, number, number | null] }) =>
          `${MONTH_LABELS[p.data[0]]} ${years[p.data[1]]}: <b>${p.data[2] ?? "N/A"}%</b>`,
        backgroundColor: dark ? "#1e293b" : "#ffffff",
        borderColor: dark ? "#334155" : "#e2e8f0",
        textStyle: { color: dark ? "#f1f5f9" : "#0f172a", fontSize: 12 },
      },
      grid: [
        { left: 55, right: 20, top: 10, height: "68%" },
        { left: 55, right: 20, top: "78%", height: "16%" },
      ],
      xAxis: [
        {
          type: "category",
          data: MONTH_LABELS,
          gridIndex: 0,
          axisLabel: { color: textColor, fontSize: 10 },
          axisLine: { show: false },
        },
        {
          type: "category",
          data: MONTH_LABELS,
          gridIndex: 1,
          axisLabel: { color: textColor, fontSize: 10 },
          axisLine: { show: false },
        },
      ],
      yAxis: [
        {
          type: "category",
          data: years,
          gridIndex: 0,
          inverse: true,
          axisLabel: { color: textColor, fontSize: 10 },
          axisLine: { show: false },
        },
        {
          scale: true,
          gridIndex: 1,
          axisLabel: { color: textColor, fontSize: 9 },
          splitLine: { lineStyle: { color: dark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" } },
        },
      ],
      visualMap: {
        min: -maxAbs,
        max: maxAbs,
        show: false,
        inRange: { color: ["#ef4444", "#f9fafb", "#22c55e"] },
      },
      series: [
        {
          type: "heatmap",
          data: heatmapData,
          xAxisIndex: 0,
          yAxisIndex: 0,
          label: {
            show: true,
            fontSize: 9,
            formatter: (p: { data: [number, number, number | null] }) =>
              p.data[2] != null ? `${p.data[2]}%` : "",
            color: dark ? "#0f172a" : "#0f172a",
          },
          emphasis: { itemStyle: { shadowBlur: 8, shadowColor: "rgba(0,0,0,0.2)" } },
        },
        {
          name: "Avg Return",
          type: "bar",
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: avgData.map((v, i) => ({
            value: v,
            itemStyle: { color: (v ?? 0) >= 0 ? "#22c55e" : "#ef4444" },
            label: { show: false },
          })),
          barMaxWidth: 28,
        },
      ],
    };
  }, [data, dark]);

  return <ReactECharts option={option} style={{ height, width: "100%" }} notMerge />;
}
