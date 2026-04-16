"use client";

import { UpcomingJobsBar } from "@/components/miner/UpcomingJobsBar";
import { JobHistoryTable } from "@/components/miner/JobHistoryTable";
import { Separator } from "@/components/ui/separator";
import { useQueryClient } from "@tanstack/react-query";
import { RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function MinerPage() {
  const qc = useQueryClient();

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Miner Stats</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Data ingestion job status and scheduling</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => qc.invalidateQueries({ queryKey: ["miner"] }).then(() => qc.invalidateQueries({ queryKey: ["upcoming"] }))}
        >
          <RefreshCcw size={14} className="mr-1.5" />
          Refresh
        </Button>
      </div>

      <UpcomingJobsBar />

      <Separator />

      <div>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Job History
        </h2>
        <JobHistoryTable />
      </div>
    </div>
  );
}
