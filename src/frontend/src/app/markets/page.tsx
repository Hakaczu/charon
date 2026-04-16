import { ExecutiveSummary } from "@/components/markets/ExecutiveSummary";
import { AssetMetricGrid } from "@/components/markets/AssetMetricGrid";
import { AssetChartGrid } from "@/components/markets/AssetChartGrid";
import { ChartLegend } from "@/components/markets/ChartLegend";
import { Separator } from "@/components/ui/separator";

export const metadata = { title: "Markets — Charon" };

export default function MarketsPage() {
  return (
    <div className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Market Overview</h1>
        <p className="text-muted-foreground text-sm mt-0.5">Live prices, signals and technical indicators</p>
      </div>

      <ExecutiveSummary />

      <div>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Market Snapshot
        </h2>
        <AssetMetricGrid />
      </div>

      <Separator />

      <div>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Charts
        </h2>
        <AssetChartGrid />
      </div>

      <ChartLegend />
    </div>
  );
}
