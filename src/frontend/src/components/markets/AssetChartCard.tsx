"use client";

import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PriceIndicatorChart } from "@/components/charts/PriceIndicatorChart";
import { SignalBadge } from "@/components/markets/SignalBadge";
import { usePrices, useAssetSignals } from "@/hooks/useMarketData";
import { calculateRSI, calculateADXProxy } from "@/lib/indicators";
import { cn } from "@/lib/utils";

interface Props {
  assetCode: string;
  assetName?: string;
}

export function AssetChartCard({ assetCode, assetName }: Props) {
  const { data: prices, isLoading: pricesLoading } = usePrices(assetCode);
  const { data: signals, isLoading: sigLoading } = useAssetSignals(assetCode);
  const loading = pricesLoading || sigLoading;

  const stats = useMemo(() => {
    if (!prices || prices.length < 14) return null;
    const sorted = [...prices].sort((a, b) => a.date.localeCompare(b.date));
    const priceVals = sorted.map((p) => p.price);

    const rsiArr = calculateRSI(priceVals);
    const adxArr = calculateADXProxy(priceVals);
    const lastRSI = rsiArr[rsiArr.length - 1];
    const lastADX = adxArr[adxArr.length - 1];
    const lastPrice = priceVals[priceVals.length - 1];
    const vol = priceVals.slice(-10).reduce((acc, v, i, arr) => {
      if (i === 0) return acc;
      return acc + Math.abs(v - arr[i - 1]);
    }, 0) / 9;

    let rsiState = "Neutral";
    if (lastRSI >= 70) rsiState = "Overbought";
    else if (lastRSI <= 30) rsiState = "Oversold";

    const trendStrength = lastADX > 25 ? "Trend" : "Range";
    const weeklyTrend = signals?.[0]?.weekly_trend ?? "N/A";

    return { lastPrice, lastRSI, lastADX, vol, rsiState, trendStrength, weeklyTrend };
  }, [prices, signals]);

  const latestSignal = signals?.[0]?.signal ?? "WAIT";

  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[350px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!prices || prices.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground text-sm">
          No data for {assetCode}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-1 pt-3 px-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold tracking-wide">
            {assetCode}
            {assetName && <span className="text-muted-foreground font-normal ml-1 text-xs">{assetName}</span>}
          </CardTitle>
          <SignalBadge signal={latestSignal} size="md" pulse />
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <PriceIndicatorChart prices={prices} signals={signals} height={320} />
        {/* Stats row */}
        {stats && (
          <div className="px-3 pb-3 pt-1 grid grid-cols-2 gap-x-4 gap-y-1 text-xs border-t border-border mt-1">
            <Stat label="Price" value={`${stats.lastPrice.toFixed(4)}`} />
            <Stat label="Volatility" value={stats.vol.toFixed(4)} />
            <Stat
              label="RSI"
              value={`${stats.lastRSI.toFixed(0)}`}
              sub={stats.rsiState}
              subColor={stats.rsiState === "Overbought" ? "red" : stats.rsiState === "Oversold" ? "green" : undefined}
            />
            <Stat
              label="Trend"
              value={stats.trendStrength}
              sub={`ADX ${stats.lastADX.toFixed(0)}`}
              subColor={stats.trendStrength === "Trend" ? "blue" : undefined}
            />
            <Stat
              label="Weekly"
              value={stats.weeklyTrend}
              subColor={
                stats.weeklyTrend === "BULLISH" ? "green" :
                stats.weeklyTrend === "BEARISH" ? "red" : undefined
              }
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function Stat({ label, value, sub, subColor }: {
  label: string; value: string; sub?: string;
  subColor?: "green" | "red" | "blue";
}) {
  const colorCls = subColor === "green" ? "text-green-500" :
    subColor === "red" ? "text-red-500" :
    subColor === "blue" ? "text-blue-500" :
    "text-muted-foreground";

  return (
    <div className="flex items-center gap-1">
      <span className="text-muted-foreground">{label}:</span>
      <span className={cn("font-medium", subColor && colorCls)}>{value}</span>
      {sub && <span className={cn("text-[10px]", colorCls)}>{sub}</span>}
    </div>
  );
}
