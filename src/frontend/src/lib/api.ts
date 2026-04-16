import type {
  Currency,
  Rate,
  GoldPrice,
  Signal,
  JobLog,
  MinerUpcoming,
  BacktestResult,
  ForecastPoint,
  CorrelationMatrix,
  SeasonalityRow,
} from "@/types/api";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(`${BASE}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

export async function fetchCurrencies(): Promise<Currency[]> {
  return get<Currency[]>("/currencies");
}

export async function fetchRates(code: string, limit = 5000): Promise<Rate[]> {
  return get<Rate[]>("/rates", { code, limit });
}

export async function fetchGold(limit = 5000): Promise<GoldPrice[]> {
  return get<GoldPrice[]>("/gold", { limit });
}

export async function fetchSignals(assetCode?: string, limit = 20): Promise<Signal[]> {
  const params: Record<string, string | number> = { limit };
  if (assetCode) params.asset_code = assetCode;
  return get<Signal[]>("/signals", params);
}

export async function fetchMinerStats(limit = 10): Promise<JobLog[]> {
  return get<JobLog[]>("/stats/miner", { limit });
}

export async function fetchUpcoming(): Promise<MinerUpcoming> {
  return get<MinerUpcoming>("/stats/upcoming");
}

export async function fetchCorrelation(): Promise<CorrelationMatrix> {
  return get<CorrelationMatrix>("/stats/correlation");
}

export async function fetchSeasonality(assetCode: string): Promise<SeasonalityRow[]> {
  return get<SeasonalityRow[]>("/stats/seasonality", { asset_code: assetCode });
}

export async function fetchForecast(assetCode: string, days = 7): Promise<ForecastPoint[]> {
  return get<ForecastPoint[]>("/predict", { asset_code: assetCode, days });
}

export async function runBacktest(assetCode: string, initialCapital: number): Promise<BacktestResult> {
  const url = new URL(`${BASE}/backtest`);
  url.searchParams.set("asset_code", assetCode);
  url.searchParams.set("initial_capital", String(initialCapital));
  const res = await fetch(url.toString(), { method: "POST" });
  if (!res.ok) throw new Error(`Backtest failed: ${res.status}`);
  return res.json() as Promise<BacktestResult>;
}
