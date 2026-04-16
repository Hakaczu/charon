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
    const text = dark ? "#64748b" : "#94a3b8";
    const grid = dark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)";

    return {
      backgroundColor: "transparent",
      animation: true,
      tooltip: {
        trigger: "axis",
        backgroundColor: dark ? "#1e293b" : "#fff",
        borderColor: dark ? "#334155" : "#e2e8f0",
        borderRadius: 8,
        textStyle: { color: dark ? "#f1f5f9" : "#0f172a", fontSize: 12 },
        formatter: (p: { name: string; value: number }[]) =>
          `${p[0]?.name}: <b>${p[0]?.value?.toFixed(2)} PLN</b>`,
      },
      dataZoom: [
        { type: "inside", start: 0, end: 100 },
        {
          type: "slider", start: 0, end: 100, height: 18, bottom: 4,
          borderColor: "transparent",
          backgroundColor: dark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.04)",
          fillerColor: dark ? "rgba(99,102,241,0.2)" : "rgba(99,102,241,0.15)",
          handleStyle: { color: "#6366f1" },
          moveHandleStyle: { color: "#6366f1" },
          textStyle: { color: "transparent" },
          showDataShadow: false,
        },
      ],
      grid: { left: 64, right: 16, top: 16, bottom: 52 },
      xAxis: {
        type: "category",
        data: data.map((d) => d.date.slice(5)),
        axisLabel: { color: text, fontSize: 9 },
        axisLine: { lineStyle: { color: grid } },
        splitLine: { show: false },
      },
      yAxis: {
        scale: true,
        axisLabel: { color: text, fontSize: 9, formatter: (v: number) => v.toFixed(0) },
        splitLine: { lineStyle: { color: grid } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: "line",
          data: data.map((d) => d.equity),
          symbol: "none",
          smooth: 0.3,
          lineStyle: { color: "#6366f1", width: 2.5 },
          areaStyle: {
            color: {
              type: "linear", x: 0, y: 0, x2: 0, y2: 1,
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
