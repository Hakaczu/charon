"use client";

import { useCorrelation } from "@/hooks/useCorrelation";
import { CorrelationHeatmap } from "@/components/charts/CorrelationHeatmap";
import { Skeleton } from "@/components/ui/skeleton";

export function CorrelationPanel() {
  const { data, isLoading, error } = useCorrelation();

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Macierz korelacji oparta na ostatnich 180 dniach danych cenowych.
        <span className="ml-2 text-blue-500 font-medium">1,0 = Idealna korelacja dodatnia.</span>
        <span className="ml-2 text-red-500 font-medium">-1,0 = Idealna korelacja ujemna.</span>
      </p>

      {isLoading && <Skeleton className="h-[500px] w-full" />}
      {error && <p className="text-sm text-destructive">Nie udało się załadować danych korelacji.</p>}
      {data && <CorrelationHeatmap data={data} />}
    </div>
  );
}
