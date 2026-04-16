import { useQuery } from "@tanstack/react-query";
import { fetchMinerStats, fetchUpcoming } from "@/lib/api";
import type { JobLog, MinerUpcoming } from "@/types/api";

export function useMinerStats(limit = 10) {
  return useQuery<JobLog[]>({
    queryKey: ["miner", limit],
    queryFn: () => fetchMinerStats(limit),
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}

export function useUpcoming() {
  return useQuery<MinerUpcoming>({
    queryKey: ["upcoming"],
    queryFn: fetchUpcoming,
    staleTime: 30_000,
    refetchInterval: 30_000,
  });
}
