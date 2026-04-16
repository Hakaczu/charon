export const APP_VERSION = "1.0.0";

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
  { href: "/markets", label: "Rynki", icon: "BarChart2" },
  { href: "/signals", label: "Sygnały", icon: "Bell" },
  { href: "/miner", label: "Miner", icon: "Activity" },
  { href: "/backtesting", label: "Backtest", icon: "FlaskConical" },
  { href: "/analysis", label: "Analiza", icon: "BrainCircuit" },
  { href: "/finances", label: "Finanse", icon: "Wallet" },
] as const;

export const MONTH_LABELS = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"];
