import { ExecutiveSummary } from "@/components/markets/ExecutiveSummary";
import { AssetMetricGrid } from "@/components/markets/AssetMetricGrid";
import { AssetChartGrid } from "@/components/markets/AssetChartGrid";
import { ChartLegend } from "@/components/markets/ChartLegend";
import { Separator } from "@/components/ui/separator";

export const metadata = { title: "Rynki — Charon" };

export default function MarketsPage() {
  return (
    <div className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Przegląd rynku</h1>
        <p className="text-muted-foreground text-sm mt-0.5">Ceny na żywo, sygnały i wskaźniki techniczne</p>
      </div>

      <ExecutiveSummary />

      <div>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Migawka rynkowa
        </h2>
        <AssetMetricGrid />
      </div>

      <Separator />

      <div>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Wykresy
        </h2>
        <AssetChartGrid />
      </div>

      <ChartLegend />
    </div>
  );
}
