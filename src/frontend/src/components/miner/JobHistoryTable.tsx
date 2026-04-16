"use client";

import { useMinerStats } from "@/hooks/useMinerStats";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

export function JobHistoryTable() {
  const { data, isLoading, error, refetch } = useMinerStats(10);

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive flex items-center justify-between">
        <span>Failed to load job history.</span>
        <button onClick={() => refetch()} className="underline text-xs">Retry</button>
      </div>
    );
  }

  function duration(started: string, finished?: string | null) {
    if (!finished) return "—";
    const ms = new Date(finished).getTime() - new Date(started).getTime();
    return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
  }

  return (
    <div className="rounded-lg border border-border overflow-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Job Type</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Started</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead className="text-right">Rows</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.map((job) => (
            <TableRow key={job.id}>
              <TableCell className="font-medium text-xs">{job.job_type}</TableCell>
              <TableCell>
                <Badge
                  variant="outline"
                  className={cn(
                    "text-[10px] uppercase",
                    job.status === "success" && "border-green-500/40 text-green-500 bg-green-500/10",
                    job.status === "error" && "border-red-500/40 text-red-500 bg-red-500/10",
                    job.status === "running" && "border-blue-500/40 text-blue-500 bg-blue-500/10"
                  )}
                >
                  {job.status}
                </Badge>
              </TableCell>
              <TableCell className="text-muted-foreground text-xs font-mono">
                {job.started_at?.slice(0, 16).replace("T", " ") ?? "—"}
              </TableCell>
              <TableCell className="text-xs font-mono">
                {duration(job.started_at, job.completed_at ?? job.finished_at)}
              </TableCell>
              <TableCell className="text-right text-xs font-mono">
                {job.rows_written ?? "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
