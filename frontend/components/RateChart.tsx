"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { HistoryPoint } from "@/lib/types";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

type Props = { code: string; series: HistoryPoint[]; avg?: number | null };

export function RateChart({ code, series, avg }: Props) {
  const labels = series.map((p) => p.date);
  const data = series.map((p) => p.value);
  const avgLine = (avg ?? (series.length ? data.reduce((a, b) => a + b, 0) / series.length : null));

  const chartData = {
    labels,
    datasets: [
      {
        label: `${code} (mid)`,
        data,
        borderColor: "#38bdf8",
        backgroundColor: "rgba(56, 189, 248, 0.15)",
        tension: 0.2,
        fill: true,
        pointRadius: 0,
        borderWidth: 2,
      },
      ...(avgLine !== null
        ? [
            {
              label: `${code} (średnia)`,
              data: data.map(() => avgLine),
              borderColor: "#facc15",
              borderWidth: 2,
              borderDash: [6, 6],
              pointRadius: 0,
              fill: false,
            },
          ]
        : []),
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        labels: { color: "#e2e8f0" },
      },
      tooltip: {
        callbacks: {
          label: (ctx: any) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(4)}`,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: "#94a3b8", maxTicksLimit: 6 },
        grid: { color: "rgba(255,255,255,0.05)" },
      },
      y: {
        ticks: { color: "#94a3b8" },
        grid: { color: "rgba(255,255,255,0.05)" },
      },
    },
  };

  return (
    <div className="chart-wrapper">
      <Line data={chartData} options={options} />
    </div>
  );
}
