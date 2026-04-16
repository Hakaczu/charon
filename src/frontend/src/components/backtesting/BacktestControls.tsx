"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCurrencies } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FlaskConical, Loader2 } from "lucide-react";
import type { Currency } from "@/types/api";

interface Props {
  onRun: (assetCode: string, capital: number) => void;
  loading?: boolean;
}

export function BacktestControls({ onRun, loading }: Props) {
  const { data: currencies } = useQuery<Currency[]>({
    queryKey: ["currencies"],
    queryFn: fetchCurrencies,
    staleTime: 3_600_000,
  });

  const options = ["GOLD", ...(currencies?.map((c) => c.code) ?? ["USD", "EUR"])];
  const [asset, setAsset] = useState("GOLD");
  const [capital, setCapital] = useState(10000);

  return (
    <div className="flex flex-wrap gap-3 items-end">
      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Asset</label>
        <Select value={asset} onValueChange={(v) => { if (v) setAsset(v); }}>
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {options.map((o) => (
              <SelectItem key={o} value={o}>{o}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1">
        <label className="text-xs text-muted-foreground">Initial Capital (PLN)</label>
        <Input
          type="number"
          value={capital}
          onChange={(e) => setCapital(Number(e.target.value))}
          className="w-40 font-mono"
          min={100}
          step={1000}
        />
      </div>

      <Button
        onClick={() => onRun(asset, capital)}
        disabled={loading}
        className="gap-1.5"
      >
        {loading ? <Loader2 size={14} className="animate-spin" /> : <FlaskConical size={14} />}
        Run Simulation
      </Button>
    </div>
  );
}
