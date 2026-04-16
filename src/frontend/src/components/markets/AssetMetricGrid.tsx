import { AssetMetricCard } from "@/components/markets/AssetMetricCard";
import { ASSETS } from "@/lib/constants";

export function AssetMetricGrid() {
  return (
    <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-2">
      {ASSETS.map((code) => (
        <AssetMetricCard key={code} assetCode={code} />
      ))}
    </div>
  );
}
