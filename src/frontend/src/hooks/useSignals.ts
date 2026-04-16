import { useQuery } from "@tanstack/react-query";
import { fetchSignals } from "@/lib/api";
import type { Signal } from "@/types/api";

export function useSignals(limit = 100) {
  return useQuery<Signal[]>({
    queryKey: ["signals", "all", limit],
    queryFn: () => fetchSignals(undefined, limit),
    staleTime: 60_000,
    refetchInterval: 60_000,
  });
}
