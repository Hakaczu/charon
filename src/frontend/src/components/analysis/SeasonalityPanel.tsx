"use client";

import { useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { SeasonalityHeatmap } from "@/components/charts/SeasonalityHeatmap";
import { Skeleton } from "@/components/ui/skeleton";
import { useSeasonality } from "@/hooks/useSeasonality";
import { ASSETS } from "@/lib/constants";
import { BarChart3 } from "lucide-react";

export function SeasonalityPanel() {
  const [asset, setAsset] = useState("GOLD");
  const [enabled, setEnabled] = useState(false);
  const { data, isLoading, error } = useSeasonality(asset, enabled);

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Analizuj historyczne miesięczne zwroty, aby zidentyfikować wzorce sezonowe.
      </p>
      <div className="flex gap-3 items-end flex-wrap">
        <div className="space-y-1">
          <label className="text-xs text-muted-foreground">Aktywo</label>
          <Select value={asset} onValueChange={(v) => { if (v) { setAsset(v); setEnabled(false); } }}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ASSETS.map((a) => (
                <SelectItem key={a} value={a}>{a}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button onClick={() => setEnabled(true)} variant="default" size="sm" className="gap-1.5">
          <BarChart3 size={14} />
          Analizuj
        </Button>
      </div>

      {isLoading && <Skeleton className="h-96 w-full" />}
      {error && <p className="text-sm text-destructive">Nie udało się załadować danych sezonowości.</p>}
      {data && data.length > 0 && <SeasonalityHeatmap data={data} />}
      {data && data.length === 0 && <p className="text-sm text-muted-foreground">Brak wystarczających danych.</p>}
    </div>
  );
}
