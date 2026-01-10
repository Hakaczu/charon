import { API_BASE } from "./config";
import { HistoryPoint, RawSnapshot, Snapshot } from "./types";

const httpError = (status: number, body: unknown) => {
  const message = typeof body === "string" ? body : JSON.stringify(body);
  return new Error(`API error ${status}: ${message}`);
};

const mapHistory = (historyMap: RawSnapshot["history_map"]): Record<string, HistoryPoint[]> =>
  Object.fromEntries(
    Object.entries(historyMap || {}).map(([code, series]) => [
      code,
      (series || []).map(([date, value]) => ({ date, value: Number(value) })),
    ])
  );

export async function fetchSnapshot(): Promise<Snapshot> {
  const res = await fetch(`${API_BASE}/api/v1/snapshot`, {
    cache: "no-store",
    next: { revalidate: 0 },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw httpError(res.status, body);
  }

  const raw = body as RawSnapshot;
  return {
    items: raw.items || [],
    history: mapHistory(raw.history_map || {}),
    lastFetch: raw.last_fetch || null,
  };
}
