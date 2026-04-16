import { Card, CardContent } from "@/components/ui/card";
import type { BacktestResult } from "@/types/api";
import { cn } from "@/lib/utils";

export function BacktestMetrics({ result }: { result: BacktestResult }) {
  const profit = result.final_value - result.initial_capital;
  const positive = profit >= 0;

  return (
    <div className="grid grid-cols-3 gap-4">
      <MetricCard
        label="Wartość końcowa"
        value={`${result.final_value.toFixed(2)} PLN`}
        sub={`${result.total_return_pct >= 0 ? "+" : ""}${result.total_return_pct.toFixed(2)}%`}
        positive={result.total_return_pct >= 0}
      />
      <MetricCard
        label="Liczba transakcji"
        value={String(result.total_trades)}
      />
      <MetricCard
        label="Zysk / Strata"
        value={`${profit >= 0 ? "+" : ""}${profit.toFixed(2)} PLN`}
        positive={positive}
      />
    </div>
  );
}

function MetricCard({ label, value, sub, positive }: {
  label: string; value: string; sub?: string; positive?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs text-muted-foreground mb-1">{label}</div>
        <div className={cn(
          "text-lg font-bold font-mono",
          positive === true && "text-green-500",
          positive === false && "text-red-500"
        )}>
          {value}
        </div>
        {sub && (
          <div className={cn("text-xs mt-0.5", positive ? "text-green-500" : "text-red-500")}>
            {sub}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
