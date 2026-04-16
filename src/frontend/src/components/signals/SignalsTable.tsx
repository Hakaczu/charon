"use client";

import { useSignals } from "@/hooks/useSignals";
import { SignalBadge } from "@/components/markets/SignalBadge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export function SignalsTable() {
  const { data: signals, isLoading, error, refetch } = useSignals(100);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive flex items-center justify-between">
        <span>Failed to load signals.</span>
        <button onClick={() => refetch()} className="underline text-xs">Retry</button>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Asset</TableHead>
            <TableHead>Signal</TableHead>
            <TableHead className="text-right">Price</TableHead>
            <TableHead className="text-right">MACD Hist</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {signals?.map((s) => (
            <TableRow key={s.id}>
              <TableCell className="text-muted-foreground text-xs font-mono">
                {s.generated_at.slice(0, 16).replace("T", " ")}
              </TableCell>
              <TableCell className="font-bold text-xs">{s.asset_code}</TableCell>
              <TableCell>
                <SignalBadge signal={s.signal} />
              </TableCell>
              <TableCell className="text-right font-mono text-xs">
                {s.price_at_signal?.toFixed(4) ?? "—"}
              </TableCell>
              <TableCell className="text-right font-mono text-xs">
                {s.histogram != null ? s.histogram.toFixed(5) : "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
