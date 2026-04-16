"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchSignals, fetchGold, fetchRates } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ASSETS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { Signal, GoldPrice, Rate } from "@/types/api";

interface BuyPosition {
  assetCode: string;
  signal: Signal;
  currentPrice: number;
}

async function fetchActiveBuyPositions(): Promise<BuyPosition[]> {
  const sigs = await fetchSignals(undefined, 100);
  const seen = new Set<string>();
  const buys: Signal[] = [];
  for (const s of sigs) {
    if (s.signal === "BUY" && ASSETS.includes(s.asset_code as typeof ASSETS[number]) && !seen.has(s.asset_code)) {
      seen.add(s.asset_code);
      buys.push(s);
    }
  }

  return Promise.all(
    buys.map(async (s) => {
      const data = s.asset_code === "GOLD"
        ? await fetchGold(1)
        : await fetchRates(s.asset_code, 1);
      const currentPrice = data.length > 0
        ? ("price" in data[0] ? Number((data[0] as GoldPrice).price) : Number((data[0] as Rate).rate_mid))
        : Number(s.price_at_signal);
      return { assetCode: s.asset_code, signal: s, currentPrice };
    })
  );
}

export function ProfitCalculator() {
  const [amount, setAmount] = useState(1000);
  const { data: positions, isLoading } = useQuery<BuyPosition[]>({
    queryKey: ["profit-calculator-positions"],
    queryFn: fetchActiveBuyPositions,
    staleTime: 60_000,
    refetchInterval: 60_000,
  });

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Calculates hypothetical return if you invested on the most recent BUY signal for each asset.
      </p>

      <div className="space-y-1 max-w-xs">
        <label className="text-xs text-muted-foreground">Investment Amount (PLN)</label>
        <Input
          type="number"
          value={amount}
          onChange={(e) => setAmount(Number(e.target.value))}
          className="font-mono"
          min={10}
          step={100}
        />
      </div>

      {isLoading && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />)}
        </div>
      )}

      {positions && positions.length === 0 && (
        <p className="text-sm text-muted-foreground">No active BUY signals found.</p>
      )}

      {positions && positions.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {positions.map(({ assetCode, signal, currentPrice }) => {
            const buyPrice = Number(signal.price_at_signal);
            const units = amount / buyPrice;
            const currentValue = units * currentPrice;
            const profit = currentValue - amount;
            const profitPct = (profit / amount) * 100;

            return (
              <Card key={assetCode}>
                <CardContent className="p-3 space-y-1">
                  <div className="font-bold text-sm">{assetCode}</div>
                  <div className="text-xs text-muted-foreground">
                    Bought at: <span className="font-mono">{buyPrice.toFixed(4)}</span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Now: <span className="font-mono">{currentPrice.toFixed(4)}</span>
                  </div>
                  <div className={cn(
                    "font-bold text-sm",
                    profitPct >= 0 ? "text-green-500" : "text-red-500"
                  )}>
                    {profit >= 0 ? "+" : ""}{profit.toFixed(2)} PLN
                  </div>
                  <div className={cn(
                    "text-xs",
                    profitPct >= 0 ? "text-green-500" : "text-red-500"
                  )}>
                    {profitPct >= 0 ? "+" : ""}{profitPct.toFixed(2)}%
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
