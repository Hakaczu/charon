import { useQuery } from "@tanstack/react-query";
import { fetchSeasonality } from "@/lib/api";
import type { SeasonalityRow } from "@/types/api";

export function useSeasonality(assetCode: string, enabled = true) {
  return useQuery<SeasonalityRow[]>({
    queryKey: ["seasonality", assetCode],
    queryFn: () => fetchSeasonality(assetCode),
    staleTime: 3_600_000,
    enabled,
  });
}
