"use client";

import ReactECharts from "echarts-for-react";
import { useTheme } from "next-themes";
import { useMemo } from "react";
import type { CorrelationMatrix } from "@/types/api";

interface Props {
  data: CorrelationMatrix;
  height?: number;
}

export function CorrelationHeatmap({ data, height = 500 }: Props) {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";

  const option = useMemo(() => {
    const assets = Object.keys(data);
    const textColor = dark ? "#94a3b8" : "#64748b";

    const heatmapData: [number, number, number][] = [];
    assets.forEach((row, i) => {
      assets.forEach((col, j) => {
        heatmapData.push([j, i, parseFloat((data[row]?.[col] ?? 0).toFixed(2))]);
      });
    });

    return {
      backgroundColor: "transparent",
      tooltip: {
        formatter: (p: { data: [number, number, number] }) =>
          `${assets[p.data[1]]} / ${assets[p.data[0]]}: <b>${p.data[2]}</b>`,
        backgroundColor: dark ? "#1e293b" : "#ffffff",
        borderColor: dark ? "#334155" : "#e2e8f0",
        textStyle: { color: dark ? "#f1f5f9" : "#0f172a", fontSize: 12 },
      },
      grid: { left: 60, right: 20, top: 20, bottom: 60 },
      xAxis: {
        type: "category",
        data: assets,
        axisLabel: { color: textColor, fontSize: 11 },
        axisLine: { show: false },
        splitArea: { show: true, areaStyle: { color: ["transparent", "transparent"] } },
      },
      yAxis: {
        type: "category",
        data: assets,
        axisLabel: { color: textColor, fontSize: 11 },
        axisLine: { show: false },
        splitArea: { show: true, areaStyle: { color: ["transparent", "transparent"] } },
      },
      visualMap: {
        min: -1,
        max: 1,
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: 0,
        inRange: { color: ["#ef4444", "#f8fafc", "#3b82f6"] },
        textStyle: { color: textColor, fontSize: 10 },
      },
      series: [
        {
          type: "heatmap",
          data: heatmapData,
          label: { show: true, fontSize: 10, color: dark ? "#1e293b" : "#0f172a" },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.3)" } },
        },
      ],
    };
  }, [data, dark]);

  return <ReactECharts option={option} style={{ height, width: "100%" }} notMerge />;
}
