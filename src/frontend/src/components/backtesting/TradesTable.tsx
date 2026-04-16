import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SignalBadge } from "@/components/markets/SignalBadge";
import type { Trade } from "@/types/api";
import { cn } from "@/lib/utils";

export function TradesTable({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) {
    return <p className="text-sm text-muted-foreground">No trades executed.</p>;
  }

  return (
    <div className="rounded-lg border border-border overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Type</TableHead>
            <TableHead className="text-right">Price</TableHead>
            <TableHead className="text-right">Units</TableHead>
            <TableHead className="text-right">Value (PLN)</TableHead>
            <TableHead className="text-right">P&L</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {trades.map((t, i) => (
            <TableRow key={i}>
              <TableCell className="font-mono text-xs text-muted-foreground">
                {t.date?.slice(0, 10)}
              </TableCell>
              <TableCell>
                <SignalBadge signal={t.type?.toUpperCase() ?? "HOLD"} />
              </TableCell>
              <TableCell className="text-right font-mono text-xs">
                {t.price?.toFixed(4) ?? "—"}
              </TableCell>
              <TableCell className="text-right font-mono text-xs">
                {t.units?.toFixed(2) ?? "—"}
              </TableCell>
              <TableCell className="text-right font-mono text-xs">
                {t.value?.toFixed(2) ?? "—"}
              </TableCell>
              <TableCell className={cn(
                "text-right font-mono text-xs font-semibold",
                t.profit != null && t.profit > 0 && "text-green-500",
                t.profit != null && t.profit < 0 && "text-red-500"
              )}>
                {t.profit != null ? `${t.profit >= 0 ? "+" : ""}${t.profit.toFixed(2)}` : "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
