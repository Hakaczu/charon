/**
 * Client-side technical indicator calculations.
 * Ported from src/shared/analysis.py — matches Python EWM/rolling logic.
 *
 * All functions expect prices sorted oldest → newest (ascending).
 */

/** Exponential Moving Average */
function ema(values: number[], span: number): number[] {
  const k = 2 / (span + 1);
  const result: number[] = new Array(values.length).fill(NaN);
  let prev = NaN;
  for (let i = 0; i < values.length; i++) {
    if (isNaN(prev)) {
      prev = values[i];
      result[i] = prev;
    } else {
      prev = values[i] * k + prev * (1 - k);
      result[i] = prev;
    }
  }
  return result;
}

export interface MACDResult {
  macd: number[];
  signal: number[];
  hist: number[];
}

export function calculateMACD(prices: number[], fast = 12, slow = 26, signal = 9): MACDResult {
  const ema12 = ema(prices, fast);
  const ema26 = ema(prices, slow);
  const macd = ema12.map((v, i) => v - ema26[i]);
  const signalLine = ema(macd, signal);
  const hist = macd.map((v, i) => v - signalLine[i]);
  return { macd, signal: signalLine, hist };
}

export function calculateRSI(prices: number[], period = 14): number[] {
  const result: number[] = new Array(prices.length).fill(NaN);
  if (prices.length < period + 1) return result;

  const gains: number[] = [];
  const losses: number[] = [];

  for (let i = 1; i < prices.length; i++) {
    const diff = prices[i] - prices[i - 1];
    gains.push(diff > 0 ? diff : 0);
    losses.push(diff < 0 ? -diff : 0);
  }

  // Initial averages (simple mean of first `period` values)
  let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
  let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;

  result[period] = 100 - 100 / (1 + avgGain / (avgLoss || 1e-10));

  for (let i = period; i < gains.length; i++) {
    avgGain = (avgGain * (period - 1) + gains[i]) / period;
    avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
    result[i + 1] = 100 - 100 / (1 + avgGain / (avgLoss || 1e-10));
  }

  return result;
}

export function calculateSMA(prices: number[], window: number): number[] {
  return prices.map((_, i) => {
    if (i < window - 1) return NaN;
    const slice = prices.slice(i - window + 1, i + 1);
    return slice.reduce((a, b) => a + b, 0) / window;
  });
}

export interface BollingerBands {
  upper: number[];
  mid: number[];
  lower: number[];
}

export function calculateBollingerBands(prices: number[], window = 20, numStd = 2): BollingerBands {
  const mid = calculateSMA(prices, window);
  const upper: number[] = [];
  const lower: number[] = [];

  for (let i = 0; i < prices.length; i++) {
    if (i < window - 1) {
      upper.push(NaN);
      lower.push(NaN);
    } else {
      const slice = prices.slice(i - window + 1, i + 1);
      const mean = mid[i];
      const variance = slice.reduce((acc, v) => acc + (v - mean) ** 2, 0) / window;
      const std = Math.sqrt(variance);
      upper.push(mean + numStd * std);
      lower.push(mean - numStd * std);
    }
  }

  return { upper, mid, lower };
}

/** Efficiency Ratio (ADX proxy) — returns 0-100 scale */
export function calculateADXProxy(prices: number[], window = 14): number[] {
  return prices.map((_, i) => {
    if (i < window) return 0;
    const slice = prices.slice(i - window, i + 1);
    const changes = slice.slice(1).map((v, j) => v - slice[j]);
    const volatility = changes.reduce((acc, c) => acc + Math.abs(c), 0);
    const direction = Math.abs(changes.reduce((acc, c) => acc + c, 0));
    if (volatility === 0) return 0;
    return (direction / volatility) * 100;
  });
}
