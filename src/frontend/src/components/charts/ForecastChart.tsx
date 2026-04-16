"use client";

import ReactECharts from "echarts-for-react";
import { useTheme } from "next-themes";
import { useMemo } from "react";
import type { ForecastPoint } from "@/types/api";

interface Props {
  data: ForecastPoint[];
  height?: number;
}

export function ForecastChart({ data, height = 320 }: Props) {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";

  const option = useMemo(() => {
    const text = dark ? "#64748b" : "#94a3b8";
    const grid = dark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)";
    const dates = data.map((d) => d.ds.slice(0, 10).slice(5));

    return {
      backgroundColor: "transparent",
      animation: true,
      tooltip: {
        trigger: "axis",
        backgroundColor: dark ? "#1e293b" : "#fff",
        borderColor: dark ? "#334155" : "#e2e8f0",
        borderRadius: 8,
        textStyle: { color: dark ? "#f1f5f9" : "#0f172a", fontSize: 11 },
      },
      grid: { left: 68, right: 16, top: 16, bottom: 28 },
      xAxis: {
        type: "category",
        data: dates,
        axisLabel: { color: text, fontSize: 9 },
        axisLine: { lineStyle: { color: grid } },
        splitLine: { show: false },
      },
      yAxis: {
        scale: true,
        axisLabel: { color: text, fontSize: 9, formatter: (v: number) => v.toFixed(4) },
        splitLine: { lineStyle: { color: grid } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        // Invisible lower bound (baseline for stacking)
        {
          name: "Lower",
          type: "line",
          data: data.map((d) => d.yhat_lower),
          lineStyle: { opacity: 0 },
          symbol: "none",
          stack: "band",
          areaStyle: { opacity: 0 },
          silent: true,
          legendHoverLink: false,
        },
        // Confidence band (upper - lower stacked on top)
        {
          name: "Przedział ufności",
          type: "line",
          data: data.map((d) => d.yhat_upper - d.yhat_lower),
          lineStyle: { opacity: 0 },
          symbol: "none",
          stack: "band",
          areaStyle: { color: "rgba(99,102,241,0.15)" },
          silent: true,
          legendHoverLink: false,
        },
        // Forecast line
        {
          name: "Prognoza",
          type: "line",
          data: data.map((d) => d.yhat),
          smooth: 0.3,
          symbol: "circle",
          symbolSize: 5,
          lineStyle: { color: "#6366f1", width: 2.5 },
          itemStyle: { color: "#6366f1" },
          label: {
            show: true,
            position: "top",
            formatter: (p: { value: number }) => p.value.toFixed(4),
            fontSize: 9,
            color: text,
          },
        },
      ],
    };
  }, [data, dark]);

  return <ReactECharts option={option} style={{ height, width: "100%" }} notMerge />;
}
