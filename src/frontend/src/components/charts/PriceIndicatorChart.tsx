"use client";

import ReactECharts from "echarts-for-react";
import { useTheme } from "next-themes";
import { useMemo } from "react";
import type { PricePoint, Signal } from "@/types/api";

interface Props {
  prices: PricePoint[];
  signals?: Signal[];
  height?: number;
}

export function PriceIndicatorChart({ prices, height = 260 }: Props) {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";

  const option = useMemo(() => {
    const sorted = [...prices].sort((a, b) => a.date.localeCompare(b.date));
    const cutoff = new Date();
    cutoff.setFullYear(cutoff.getFullYear() - 1);
    const display = sorted.filter((p) => new Date(p.date) >= cutoff);

    const text = dark ? "#64748b" : "#94a3b8";
    const grid = dark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)";

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
          `${p[0]?.name}: <b>${p[0]?.value?.toFixed(4)}</b>`,
      },
      grid: { left: 56, right: 12, top: 12, bottom: 28 },
      xAxis: {
        type: "category",
        data: display.map((p) => p.date.slice(5)),
        axisLabel: { color: text, fontSize: 9 },
        axisLine: { lineStyle: { color: grid } },
        splitLine: { show: false },
      },
      yAxis: {
        scale: true,
        axisLabel: { color: text, fontSize: 9, formatter: (v: number) => v.toFixed(3) },
        splitLine: { lineStyle: { color: grid } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: "line",
          data: display.map((p) => p.price),
          symbol: "none",
          smooth: 0.3,
          lineStyle: { color: "#6366f1", width: 2.5 },
          areaStyle: {
            color: {
              type: "linear", x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(99,102,241,0.3)" },
                { offset: 1, color: "rgba(99,102,241,0.02)" },
              ],
            },
          },
          itemStyle: { color: "#6366f1" },
        },
      ],
    };
  }, [prices, dark]);

  return <ReactECharts option={option} style={{ height, width: "100%" }} notMerge lazyUpdate />;
}
