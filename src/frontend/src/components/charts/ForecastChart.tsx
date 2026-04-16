"use client";

import ReactECharts from "echarts-for-react";
import { useTheme } from "next-themes";
import { useMemo } from "react";
import { CHART_COLORS } from "@/lib/constants";
import type { ForecastPoint } from "@/types/api";

interface Props {
  data: ForecastPoint[];
  height?: number;
}

export function ForecastChart({ data, height = 320 }: Props) {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";

  const option = useMemo(() => {
    const textColor = dark ? "#94a3b8" : "#64748b";
    const gridColor = dark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)";
    const dates = data.map((d) => d.ds.slice(0, 10));

    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: dark ? "#1e293b" : "#ffffff",
        borderColor: dark ? "#334155" : "#e2e8f0",
        textStyle: { color: dark ? "#f1f5f9" : "#0f172a", fontSize: 12 },
      },
      grid: { left: 65, right: 20, top: 20, bottom: 30 },
      xAxis: {
        type: "category",
        data: dates,
        axisLabel: { color: textColor, fontSize: 9 },
        axisLine: { lineStyle: { color: gridColor } },
        splitLine: { show: false },
      },
      yAxis: {
        scale: true,
        axisLabel: { color: textColor, fontSize: 9, formatter: (v: number) => v.toFixed(4) },
        splitLine: { lineStyle: { color: gridColor } },
      },
      series: [
        // Lower confidence bound (invisible baseline for fill)
        {
          name: "Lower",
          type: "line",
          data: data.map((d) => d.yhat_lower),
          lineStyle: { opacity: 0 },
          symbol: "none",
          stack: "confidence",
          areaStyle: { opacity: 0 },
          silent: true,
        },
        // Upper - lower = the band (filled)
        {
          name: "Confidence",
          type: "line",
          data: data.map((d) => d.yhat_upper - d.yhat_lower),
          lineStyle: { opacity: 0 },
          symbol: "none",
          stack: "confidence",
          areaStyle: { color: CHART_COLORS.forecastBand, origin: "start" },
          silent: true,
        },
        // Forecast line
        {
          name: "Forecast",
          type: "line",
          data: data.map((d) => d.yhat),
          lineStyle: { color: CHART_COLORS.forecastLine, width: 2.5 },
          symbol: "circle",
          symbolSize: 4,
          itemStyle: { color: CHART_COLORS.forecastLine },
          label: {
            show: true,
            position: "top",
            formatter: (p: { value: number }) => p.value.toFixed(4),
            fontSize: 9,
            color: textColor,
          },
        },
      ],
    };
  }, [data, dark]);

  return <ReactECharts option={option} style={{ height, width: "100%" }} notMerge />;
}
