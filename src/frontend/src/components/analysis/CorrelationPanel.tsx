"use client";

import { useCorrelation } from "@/hooks/useCorrelation";
import { CorrelationHeatmap } from "@/components/charts/CorrelationHeatmap";
import { Skeleton } from "@/components/ui/skeleton";

export function CorrelationPanel() {
  const { data, isLoading, error } = useCorrelation();

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Correlation matrix based on the last 180 days of price data.
        <span className="ml-2 text-blue-500 font-medium">1.0 = Perfect positive.</span>
        <span className="ml-2 text-red-500 font-medium">-1.0 = Perfect negative.</span>
      </p>

      {isLoading && <Skeleton className="h-[500px] w-full" />}
      {error && <p className="text-sm text-destructive">Failed to load correlation data.</p>}
      {data && <CorrelationHeatmap data={data} />}
    </div>
  );
}
