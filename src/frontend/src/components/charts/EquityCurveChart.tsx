"use client";

import ReactECharts from "echarts-for-react";
import { useTheme } from "next-themes";
import { useMemo } from "react";
import type { EquityPoint } from "@/types/api";

interface Props {
  data: EquityPoint[];
  height?: number;
}

export function EquityCurveChart({ data, height = 300 }: Props) {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";

  const option = useMemo(() => {
    const textColor = dark ? "#94a3b8" : "#64748b";
    const gridColor = dark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)";

    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: dark ? "#1e293b" : "#ffffff",
        borderColor: dark ? "#334155" : "#e2e8f0",
        textStyle: { color: dark ? "#f1f5f9" : "#0f172a", fontSize: 12 },
        formatter: (params: { name: string; value: number }[]) =>
          `${params[0]?.name}: <b>${params[0]?.value?.toFixed(2)} PLN</b>`,
      },
      grid: { left: 70, right: 20, top: 20, bottom: 30 },
      xAxis: {
        type: "category",
        data: data.map((d) => d.date),
        axisLabel: { color: textColor, fontSize: 9 },
        axisLine: { lineStyle: { color: gridColor } },
        splitLine: { show: false },
      },
      yAxis: {
        scale: true,
        axisLabel: { color: textColor, fontSize: 9, formatter: (v: number) => `${v.toFixed(0)}` },
        splitLine: { lineStyle: { color: gridColor } },
      },
      series: [
        {
          name: "Portfolio Value",
          type: "line",
          data: data.map((d) => d.equity),
          symbol: "none",
          lineStyle: { color: "#6366f1", width: 2 },
          areaStyle: {
            color: {
              type: "linear",
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(99,102,241,0.35)" },
                { offset: 1, color: "rgba(99,102,241,0.02)" },
              ],
            },
          },
          itemStyle: { color: "#6366f1" },
        },
      ],
    };
  }, [data, dark]);

  return <ReactECharts option={option} style={{ height, width: "100%" }} notMerge />;
}
