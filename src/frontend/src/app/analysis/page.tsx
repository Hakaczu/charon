"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CorrelationPanel } from "@/components/analysis/CorrelationPanel";
import { SeasonalityPanel } from "@/components/analysis/SeasonalityPanel";
import { ForecastPanel } from "@/components/analysis/ForecastPanel";
import { ProfitCalculator } from "@/components/analysis/ProfitCalculator";
import { Flame, CalendarDays, BrainCircuit, DollarSign } from "lucide-react";

export default function AnalysisPage() {
  return (
    <div className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Advanced Analysis</h1>
        <p className="text-muted-foreground text-sm mt-0.5">Correlation, seasonality, AI forecasting and profit simulation</p>
      </div>

      <Tabs defaultValue="correlation">
        <TabsList className="flex-wrap h-auto gap-1">
          <TabsTrigger value="correlation" className="gap-1.5 text-xs">
            <Flame size={13} /> Correlation
          </TabsTrigger>
          <TabsTrigger value="seasonality" className="gap-1.5 text-xs">
            <CalendarDays size={13} /> Seasonality
          </TabsTrigger>
          <TabsTrigger value="forecast" className="gap-1.5 text-xs">
            <BrainCircuit size={13} /> AI Forecast
          </TabsTrigger>
          <TabsTrigger value="profit" className="gap-1.5 text-xs">
            <DollarSign size={13} /> Profit Calc
          </TabsTrigger>
        </TabsList>

        <TabsContent value="correlation" className="mt-6">
          <CorrelationPanel />
        </TabsContent>

        <TabsContent value="seasonality" className="mt-6">
          <SeasonalityPanel />
        </TabsContent>

        <TabsContent value="forecast" className="mt-6">
          <ForecastPanel />
        </TabsContent>

        <TabsContent value="profit" className="mt-6">
          <ProfitCalculator />
        </TabsContent>
      </Tabs>
    </div>
  );
}
