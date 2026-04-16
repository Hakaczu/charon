"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { SignalBadge } from "@/components/markets/SignalBadge";
import { fetchGold, fetchRates, fetchSignals } from "@/lib/api";
import { ASSETS } from "@/lib/constants";
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Zap } from "lucide-react";

interface SummaryData {
  sentiment: string;
  upCount: number;
  downCount: number;
  topGainer: { code: string; pct: number } | null;
  topLoser: { code: string; pct: number } | null;
  rsiAlerts: string[];
  featuredSignal: { asset_code: string; signal: string; generated_at: string } | null;
}

async function buildSummary(): Promise<SummaryData> {
  let upCount = 0;
  let downCount = 0;
  let topGainer: SummaryData["topGainer"] = null;
  let topLoser: SummaryData["topLoser"] = null;

  // Fetch last 2 prices per asset for delta
  await Promise.all(
    ASSETS.map(async (code) => {
      const data =
        code === "GOLD"
          ? await fetchGold(2)
          : await fetchRates(code, 2);
      if (data.length < 2) return;
      const curr = "price" in data[0] ? Number((data[0] as { price: number }).price) : Number((data[0] as { rate_mid: number }).rate_mid);
      const prev = "price" in data[1] ? Number((data[1] as { price: number }).price) : Number((data[1] as { rate_mid: number }).rate_mid);
      const pct = ((curr - prev) / prev) * 100;
      if (pct > 0) upCount++;
      else downCount++;
      if (!topGainer || pct > topGainer.pct) topGainer = { code, pct };
      if (!topLoser || pct < topLoser.pct) topLoser = { code, pct };
    })
  );

  const sigs = await fetchSignals(undefined, 30);
  const rsiAlertsSet = new Set<string>();
  let featuredSignal: SummaryData["featuredSignal"] = null;

  for (const s of sigs) {
    if (!featuredSignal && s.signal === "BUY") {
      featuredSignal = { asset_code: s.asset_code, signal: s.signal, generated_at: s.generated_at };
    }
    if (s.rsi != null) {
      if (s.rsi > 70) rsiAlertsSet.add(`${s.asset_code} Wykupienie (RSI ${s.rsi.toFixed(0)})`);
      if (s.rsi < 30) rsiAlertsSet.add(`${s.asset_code} Wyprzedanie (RSI ${s.rsi.toFixed(0)})`);
    }
  }

  let sentiment = "Neutralny";
  if (upCount > downCount + 2) sentiment = "Wzrostowy";
  else if (downCount > upCount + 2) sentiment = "Spadkowy";

  return {
    sentiment,
    upCount,
    downCount,
    topGainer,
    topLoser,
    rsiAlerts: [...rsiAlertsSet].slice(0, 3),
    featuredSignal,
  };
}

export function ExecutiveSummary() {
  const { data, isLoading } = useQuery<SummaryData>({
    queryKey: ["executive-summary"],
    queryFn: buildSummary,
    staleTime: 60_000,
    refetchInterval: 60_000,
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-48" />
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const SentimentIcon =
    data.sentiment === "Wzrostowy" ? TrendingUp :
    data.sentiment === "Spadkowy" ? TrendingDown : Minus;

  const sentimentColor =
    data.sentiment === "Wzrostowy" ? "text-green-500" :
    data.sentiment === "Spadkowy" ? "text-red-500" : "text-muted-foreground";

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          Podsumowanie rynku
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Left: sentiment + movers + alerts */}
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              <SentimentIcon size={18} className={sentimentColor} />
              <span className="font-semibold">{data.sentiment}</span>
              <span className="text-sm text-muted-foreground">
                — {data.upCount} wzrosty, {data.downCount} spadki
              </span>
            </div>

            <div className="flex flex-wrap gap-3 text-sm">
              {data.topGainer && (
                <span className="flex items-center gap-1 text-green-500">
                  <TrendingUp size={14} />
                  <strong>{data.topGainer.code}</strong>
                  +{data.topGainer.pct.toFixed(2)}%
                </span>
              )}
              {data.topLoser && (
                <span className="flex items-center gap-1 text-red-500">
                  <TrendingDown size={14} />
                  <strong>{data.topLoser.code}</strong>
                  {data.topLoser.pct.toFixed(2)}%
                </span>
              )}
            </div>

            {data.rsiAlerts.length > 0 && (
              <div className="flex items-start gap-1.5 text-xs text-amber-600 dark:text-amber-400">
                <AlertTriangle size={13} className="shrink-0 mt-0.5" />
                <span>{data.rsiAlerts.join("  •  ")}</span>
              </div>
            )}
          </div>

          {/* Right: Signal of the day */}
          <div className="sm:w-52 shrink-0">
            {data.featuredSignal ? (
              <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-3 space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-green-600 dark:text-green-400">
                  <Zap size={12} />
                  Sygnał dnia
                </div>
                <div className="font-bold text-lg">{data.featuredSignal.asset_code}</div>
                <SignalBadge signal={data.featuredSignal.signal} size="md" pulse />
                <div className="text-xs text-muted-foreground mt-1">
                  {data.featuredSignal.generated_at.slice(0, 10)}
                </div>
              </div>
            ) : (
              <div className="rounded-lg border border-border bg-muted/30 p-3 text-sm text-muted-foreground">
                Brak silnych sygnałów.
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
