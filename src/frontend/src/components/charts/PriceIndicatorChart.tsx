"use client";

import { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import { useTheme } from "next-themes";
import { calculateRSI, calculateSMA } from "@/lib/indicators";
import { SIGNAL_COLORS } from "@/lib/constants";
import type { PricePoint, Signal } from "@/types/api";

interface Props {
  prices: PricePoint[];
  signals?: Signal[];
  height?: number;
}

const PRICE_COLOR = "#6366f1"; // indigo — cleaner than electric blue
const SMA_COLOR   = "#f59e0b"; // amber
const RSI_COLOR   = "#8b5cf6"; // violet

export function PriceIndicatorChart({ prices, signals = [], height = 310 }: Props) {
  const { resolvedTheme } = useTheme();
  const dark = resolvedTheme === "dark";

  const option = useMemo(() => {
    const sorted = [...prices].sort((a, b) => a.date.localeCompare(b.date));

    // Last 365 days
    const cutoff = new Date();
    cutoff.setFullYear(cutoff.getFullYear() - 1);
    const display = sorted.filter((p) => new Date(p.date) >= cutoff);
    if (display.length === 0) return {};

    const dates     = display.map((p) => p.date);
    const priceVals = display.map((p) => p.price);

    // Indicators calculated on full history, sliced to display window
    const allPrices = sorted.map((p) => p.price);
    const startIdx  = sorted.length - display.length;

    const rsiAll  = calculateRSI(allPrices);
    const sma50All = calculateSMA(allPrices, 50);

    const rsiSlice  = rsiAll.slice(startIdx);
    const sma50Slice = sma50All.slice(startIdx);

    // Signal markers
    const buyMarkers:  [string, number][] = [];
    const sellMarkers: [string, number][] = [];
    signals.forEach((s) => {
      const date = s.generated_at.slice(0, 10);
      const idx  = dates.indexOf(date);
      if (idx === -1) return;
      if (s.signal === "BUY")  buyMarkers.push([date, priceVals[idx]]);
      if (s.signal === "SELL") sellMarkers.push([date, priceVals[idx]]);
    });

    const textColor = dark ? "#64748b" : "#94a3b8";
    const gridLine  = dark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)";
    const tooltipBg = dark ? "#1e293b" : "#fff";
    const tooltipBorder = dark ? "#334155" : "#e2e8f0";
    const tooltipText   = dark ? "#f1f5f9" : "#0f172a";

    return {
      backgroundColor: "transparent",
      animation: false,
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "line", lineStyle: { color: textColor, width: 1, type: "dashed" } },
        backgroundColor: tooltipBg,
        borderColor: tooltipBorder,
        borderRadius: 8,
        textStyle: { color: tooltipText, fontSize: 11, fontFamily: "var(--font-mono)" },
      },
      axisPointer: { link: [{ xAxisIndex: "all" }] },
      dataZoom: [
        { type: "inside", xAxisIndex: [0, 1], start: 0, end: 100 },
      ],
      grid: [
        // Price panel — tall
        { left: 52, right: 8, top: 8, bottom: "34%" },
        // RSI panel — compact
        { left: 52, right: 8, top: "72%", bottom: 8 },
      ],
      xAxis: [
        {
          type: "category",
          data: dates,
          gridIndex: 0,
          show: false,
        },
        {
          type: "category",
          data: dates,
          gridIndex: 1,
          axisLabel: {
            color: textColor,
            fontSize: 9,
            fontFamily: "var(--font-mono)",
            formatter: (v: string) => v.slice(5), // MM-DD
          },
          axisLine: { lineStyle: { color: gridLine } },
          splitLine: { show: false },
        },
      ],
      yAxis: [
        {
          scale: true,
          gridIndex: 0,
          splitLine: { lineStyle: { color: gridLine } },
          axisLabel: {
            color: textColor,
            fontSize: 9,
            fontFamily: "var(--font-mono)",
            formatter: (v: number) => v.toFixed(3),
          },
          position: "left",
        },
        {
          min: 0,
          max: 100,
          gridIndex: 1,
          interval: 35,
          splitLine: { show: false },
          axisLabel: {
            color: textColor,
            fontSize: 9,
            fontFamily: "var(--font-mono)",
          },
        },
      ],
      series: [
        // Price
        {
          name: "Price",
          type: "line",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: priceVals,
          lineStyle: { color: PRICE_COLOR, width: 2 },
          symbol: "none",
          itemStyle: { color: PRICE_COLOR },
          areaStyle: {
            color: {
              type: "linear", x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: `${PRICE_COLOR}22` },
                { offset: 1, color: `${PRICE_COLOR}00` },
              ],
            },
          },
        },
        // SMA 50
        {
          name: "SMA 50",
          type: "line",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: sma50Slice.map((v) => (isNaN(v) ? null : v)),
          lineStyle: { color: SMA_COLOR, width: 1.5, type: "dashed" },
          symbol: "none",
          itemStyle: { color: SMA_COLOR },
        },
        // BUY markers
        {
          name: "BUY",
          type: "scatter",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: buyMarkers,
          symbol: "triangle",
          symbolSize: 9,
          itemStyle: { color: SIGNAL_COLORS.BUY },
          z: 10,
        },
        // SELL markers
        {
          name: "SELL",
          type: "scatter",
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: sellMarkers,
          symbol: "triangle",
          symbolRotate: 180,
          symbolSize: 9,
          itemStyle: { color: SIGNAL_COLORS.SELL },
          z: 10,
        },
        // RSI
        {
          name: "RSI",
          type: "line",
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: rsiSlice.map((v) => (isNaN(v) ? null : parseFloat(v.toFixed(1)))),
          lineStyle: { color: RSI_COLOR, width: 1.5 },
          symbol: "none",
          itemStyle: { color: RSI_COLOR },
          markLine: {
            silent: true,
            symbol: "none",
            lineStyle: { type: "dashed", width: 1 },
            data: [
              {
                yAxis: 70,
                lineStyle: { color: "#ef444488" },
                label: { formatter: "OB 70", color: "#ef4444", fontSize: 8, position: "insideEndTop" },
              },
              {
                yAxis: 30,
                lineStyle: { color: "#22c55e88" },
                label: { formatter: "OS 30", color: "#22c55e", fontSize: 8, position: "insideEndBottom" },
              },
            ],
          },
        },
      ],
    };
  }, [prices, signals, dark]);

  return (
    <ReactECharts
      option={option}
      style={{ height, width: "100%" }}
      notMerge
      lazyUpdate
    />
  );
}
