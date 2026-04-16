"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PriceIndicatorChart } from "@/components/charts/PriceIndicatorChart";
import { SignalBadge } from "@/components/markets/SignalBadge";
import { usePrices, useAssetSignals } from "@/hooks/useMarketData";

interface Props {
  assetCode: string;
  assetName?: string;
}

export function AssetChartCard({ assetCode, assetName }: Props) {
  const { data: prices, isLoading: pricesLoading } = usePrices(assetCode);
  const { data: signals, isLoading: sigLoading } = useAssetSignals(assetCode);
  const loading = pricesLoading || sigLoading;

  const latestSignal = signals?.[0]?.signal ?? "WAIT";

  if (loading) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[260px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!prices || prices.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground text-sm">
          Brak danych dla {assetCode}
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
            {assetName && (
              <span className="text-muted-foreground font-normal ml-1 text-xs">{assetName}</span>
            )}
          </CardTitle>
          <SignalBadge signal={latestSignal} size="md" pulse />
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <PriceIndicatorChart prices={prices} height={260} />
      </CardContent>
    </Card>
  );
}
