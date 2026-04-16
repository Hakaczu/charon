import { AssetChartCard } from "@/components/markets/AssetChartCard";
import { CHART_ASSETS } from "@/lib/constants";

// Display names for chart labels
const ASSET_NAMES: Record<string, string> = {
  GOLD: "Gold (1g)",
  USD: "US Dollar",
  EUR: "Euro",
  CHF: "Swiss Franc",
  GBP: "British Pound",
  JPY: "Japanese Yen",
  CAD: "Canadian Dollar",
  AUD: "Australian Dollar",
};

export function AssetChartGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {CHART_ASSETS.map((code) => (
        <AssetChartCard key={code} assetCode={code} assetName={ASSET_NAMES[code]} />
      ))}
    </div>
  );
}
