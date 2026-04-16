"use client";

import { useUpcoming } from "@/hooks/useMinerStats";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Clock, Database, Coins } from "lucide-react";

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return iso;
  }
}

export function UpcomingJobsBar() {
  const { data, isLoading } = useUpcoming();

  if (isLoading) {
    return (
      <div className="grid grid-cols-3 gap-4">
        {[0, 1, 2].map((i) => <Skeleton key={i} className="h-20" />)}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="grid grid-cols-3 gap-4">
      <JobCard icon={<Database size={16} />} label="Next Rates Import" value={formatTime(data.import_rates)} />
      <JobCard icon={<Coins size={16} />} label="Next Gold Import" value={formatTime(data.import_gold)} />
      <JobCard icon={<Clock size={16} />} label="Server Time" value={formatTime(data.server_time)} />
    </div>
  );
}

function JobCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 text-muted-foreground text-xs mb-1">
          {icon}
          {label}
        </div>
        <div className="font-mono text-lg font-semibold">{value}</div>
      </CardContent>
    </Card>
  );
}
