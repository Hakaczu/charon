import { useMutation } from "@tanstack/react-query";
import { runBacktest } from "@/lib/api";
import type { BacktestResult } from "@/types/api";

export function useBacktest() {
  return useMutation<BacktestResult, Error, { assetCode: string; initialCapital: number }>({
    mutationFn: ({ assetCode, initialCapital }) => runBacktest(assetCode, initialCapital),
  });
}
