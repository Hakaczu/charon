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
import { ForecastChart } from "@/components/charts/ForecastChart";
import { Skeleton } from "@/components/ui/skeleton";
import { useForecast } from "@/hooks/useForecast";
import { ASSETS } from "@/lib/constants";
import { BrainCircuit, Loader2 } from "lucide-react";

export function ForecastPanel() {
  const [asset, setAsset] = useState("GOLD");
  const [enabled, setEnabled] = useState(false);
  const { data, isLoading, error } = useForecast(asset, 7, enabled);

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Prognoza ceny na 7 dni oparta na AI (Facebook Prophet).
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
        <Button
          onClick={() => setEnabled(true)}
          variant="default"
          size="sm"
          disabled={isLoading}
          className="gap-1.5"
        >
          {isLoading ? <Loader2 size={14} className="animate-spin" /> : <BrainCircuit size={14} />}
          Uruchom prognozę AI
        </Button>
      </div>

      {isLoading && <Skeleton className="h-80 w-full" />}
      {error && <p className="text-sm text-destructive">Prognoza nie powiodła się.</p>}
      {data && data.length > 0 && (
        <div>
          <p className="text-xs text-muted-foreground mb-2">
            7-dniowa prognoza dla <strong>{asset}</strong> — obszar zacieniowany = 80% przedział ufności
          </p>
          <ForecastChart data={data} />
        </div>
      )}
    </div>
  );
}
