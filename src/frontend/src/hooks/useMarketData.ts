import { useQuery } from "@tanstack/react-query";
import { fetchRates, fetchGold, fetchSignals } from "@/lib/api";
import type { PricePoint } from "@/types/api";
import type { Rate, GoldPrice, Signal } from "@/types/api";

export function usePrices(assetCode: string) {
  return useQuery({
    queryKey: ["prices", assetCode],
    queryFn: async (): Promise<PricePoint[]> => {
      if (assetCode === "GOLD") {
        const data: GoldPrice[] = await fetchGold(5000);
        return data.map((d) => ({ date: d.effective_date, price: Number(d.price) }));
      }
      const data: Rate[] = await fetchRates(assetCode, 5000);
      return data.map((d) => ({ date: d.effective_date, price: Number(d.rate_mid) }));
    },
    staleTime: 60_000,
    refetchInterval: 60_000,
  });
}

export function useAssetSignals(assetCode: string, limit = 20) {
  return useQuery<Signal[]>({
    queryKey: ["signals", assetCode],
    queryFn: () => fetchSignals(assetCode, limit),
    staleTime: 60_000,
    refetchInterval: 60_000,
  });
}

/** Fetches last 2 price points for the metric card delta calculation */
export function useLatestPrice(assetCode: string) {
  return useQuery({
    queryKey: ["latestPrice", assetCode],
    queryFn: async () => {
      if (assetCode === "GOLD") {
        const data = await fetchGold(2);
        return data.map((d) => ({ date: d.effective_date, price: Number(d.price) }));
      }
      const data = await fetchRates(assetCode, 2);
      return data.map((d) => ({ date: d.effective_date, price: Number(d.rate_mid) }));
    },
    staleTime: 60_000,
    refetchInterval: 60_000,
  });
}

export function useLatestSignal(assetCode: string) {
  return useQuery<Signal[]>({
    queryKey: ["latestSignal", assetCode],
    queryFn: () => fetchSignals(assetCode, 1),
    staleTime: 60_000,
    refetchInterval: 60_000,
  });
}
