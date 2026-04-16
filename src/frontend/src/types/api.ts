export interface Currency {
  id: number;
  code: string;
  name: string;
  active: boolean;
}

export interface Rate {
  id: number;
  currency_code: string;
  effective_date: string;
  rate_mid: number;
  rate_buy?: number | null;
  rate_sell?: number | null;
}

export interface GoldPrice {
  id: number;
  effective_date: string;
  price: number;
}

export type SignalType = "BUY" | "SELL" | "HOLD";

export interface Signal {
  id: number;
  asset_code: string;
  signal: SignalType;
  generated_at: string;
  price_at_signal: number;
  histogram?: number | null;
  rsi?: number | null;
  adx?: number | null;
  weekly_trend?: string | null;
}

export interface JobLog {
  id: number;
  job_type: string;
  status: string;
  started_at: string;
  finished_at?: string | null;
  completed_at?: string | null;
  rows_written?: number | null;
  error_message?: string | null;
}

export interface MinerUpcoming {
  import_rates: string;
  import_gold: string;
  server_time: string;
}

export interface EquityPoint {
  date: string;
  equity: number;
}

export interface Trade {
  date: string;
  type: string;
  price: number;
  units?: number | null;
  value?: number | null;
  profit?: number | null;
}

export interface BacktestResult {
  initial_capital: number;
  final_value: number;
  total_return_pct: number;
  total_trades: number;
  trades: Trade[];
  equity_curve: EquityPoint[];
}

export interface ForecastPoint {
  ds: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
}

export type CorrelationMatrix = Record<string, Record<string, number>>;

export interface SeasonalityRow {
  year: number;
  [month: number]: number;
}

// Unified price point used internally (normalised from Rate | GoldPrice)
export interface PricePoint {
  date: string;
  price: number;
}
