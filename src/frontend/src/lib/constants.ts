export const ASSETS = ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD", "NOK"] as const;
export type AssetCode = (typeof ASSETS)[number];

export const PRIORITY_ORDER = ["USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD", "NOK"] as const;

export const CHART_ASSETS = ["GOLD", "USD", "EUR", "CHF", "GBP", "JPY", "CAD", "AUD"] as const;

export const SIGNAL_COLORS = {
  BUY: "#00C853",
  SELL: "#D50000",
  HOLD: "#888888",
  NEUTRAL: "#888888",
} as const;

export const CHART_COLORS = {
  price: "#2962FF",
  sma50: "#FF6D00",
  rsi: "#7E57C2",
  macdPositive: "#00C853",
  macdNegative: "#D50000",
  bbFill: "rgba(128, 128, 128, 0.15)",
  forecastLine: "#00B6F4",
  forecastBand: "rgba(0, 182, 246, 0.2)",
} as const;

export const NAV_ITEMS = [
  { href: "/markets", label: "Markets", icon: "BarChart2" },
  { href: "/signals", label: "Signals", icon: "Bell" },
  { href: "/miner", label: "Miner", icon: "Activity" },
  { href: "/backtesting", label: "Backtest", icon: "FlaskConical" },
  { href: "/analysis", label: "Analysis", icon: "BrainCircuit" },
  { href: "/finances", label: "Finances", icon: "Wallet" },
] as const;

export const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
