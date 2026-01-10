import { Analytics, HistoryPoint } from "./types";

export const computeAnalytics = (series: HistoryPoint[]): Analytics => {
  if (!series.length) {
    return { avg: null, min: null, max: null, std: null, last: null, lastDate: null };
  }
  const values = series.map((p) => p.value);
  const n = values.length;
  const avg = values.reduce((acc, v) => acc + v, 0) / n;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const last = values[values.length - 1];
  const lastDate = series[series.length - 1]?.date ?? null;
  const variance = values.reduce((acc, v) => acc + Math.pow(v - avg, 2), 0) / n;
  const std = Math.sqrt(variance);
  return { avg, min, max, std, last, lastDate };
};

export const computeAnalyticsMap = (history: Record<string, HistoryPoint[]>): Record<string, Analytics> => {
  return Object.fromEntries(Object.entries(history).map(([code, series]) => [code, computeAnalytics(series)]));
};
