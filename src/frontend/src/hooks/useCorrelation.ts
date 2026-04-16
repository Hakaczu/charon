import { useQuery } from "@tanstack/react-query";
import { fetchCorrelation } from "@/lib/api";
import type { CorrelationMatrix } from "@/types/api";

export function useCorrelation() {
  return useQuery<CorrelationMatrix>({
    queryKey: ["correlation"],
    queryFn: fetchCorrelation,
    staleTime: 3_600_000,
  });
}
