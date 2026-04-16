import { useQuery } from "@tanstack/react-query";
import { fetchForecast } from "@/lib/api";
import type { ForecastPoint } from "@/types/api";

export function useForecast(assetCode: string, days = 7, enabled = true) {
  return useQuery<ForecastPoint[]>({
    queryKey: ["forecast", assetCode, days],
    queryFn: () => fetchForecast(assetCode, days),
    staleTime: 3_600_000,
    enabled,
  });
}
