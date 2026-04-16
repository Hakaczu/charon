"use client";

import { BacktestControls } from "@/components/backtesting/BacktestControls";
import { BacktestMetrics } from "@/components/backtesting/BacktestMetrics";
import { TradesTable } from "@/components/backtesting/TradesTable";
import { EquityCurveChart } from "@/components/charts/EquityCurveChart";
import { Separator } from "@/components/ui/separator";
import { useBacktest } from "@/hooks/useBacktest";

export default function BacktestingPage() {
  const { mutate, data, isPending, error } = useBacktest();

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Backtesting strategii</h1>
        <p className="text-muted-foreground text-sm mt-0.5">Symuluj strategię Charona na danych historycznych</p>
      </div>

      <BacktestControls onRun={(asset, capital) => mutate({ assetCode: asset, initialCapital: capital })} loading={isPending} />

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          Symulacja nie powiodła się: {error.message}
        </div>
      )}

      {data && (
        <>
          <Separator />
          <BacktestMetrics result={data} />

          {data.equity_curve.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Wartość portfela w czasie
              </h2>
              <EquityCurveChart data={data.equity_curve} height={280} />
            </div>
          )}

          <div>
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Historia transakcji
            </h2>
            <TradesTable trades={data.trades} />
          </div>
        </>
      )}
    </div>
  );
}
