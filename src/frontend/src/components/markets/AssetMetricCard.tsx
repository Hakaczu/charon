"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { SignalBadge } from "@/components/markets/SignalBadge";
import { useLatestPrice, useLatestSignal } from "@/hooks/useMarketData";
import { cn } from "@/lib/utils";

interface Props {
  assetCode: string;
}

export function AssetMetricCard({ assetCode }: Props) {
  const { data: prices, isLoading: pricesLoading } = useLatestPrice(assetCode);
  const { data: signals, isLoading: sigLoading } = useLatestSignal(assetCode);
  const loading = pricesLoading || sigLoading;

  if (loading) {
    return (
      <Card className="p-2">
        <CardContent className="p-0 space-y-1">
          <Skeleton className="h-3 w-10" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-3 w-8" />
        </CardContent>
      </Card>
    );
  }

  const current = prices?.[0]?.price;
  const prev = prices?.[1]?.price;
  const delta = current != null && prev != null ? ((current - prev) / prev) * 100 : null;
  const signal = signals?.[0]?.signal ?? "WAIT";

  return (
    <Card className="p-2 cursor-default hover:ring-1 hover:ring-primary/30 transition-all">
      <CardContent className="p-0">
        <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-0.5">
          {assetCode}
        </div>
        <div className="font-mono text-sm font-semibold leading-tight">
          {current != null ? current.toFixed(4) : "—"}
        </div>
        <div className="flex items-center gap-1 mt-0.5 flex-wrap">
          {delta != null && (
            <span
              className={cn(
                "text-[10px] font-medium",
                delta > 0 ? "text-green-500" : delta < 0 ? "text-red-500" : "text-muted-foreground"
              )}
            >
              {delta > 0 ? "+" : ""}{delta.toFixed(2)}%
            </span>
          )}
          <SignalBadge signal={signal} pulse />
        </div>
      </CardContent>
    </Card>
  );
}
