"use client";

import { useEffect, useState } from "react";
import { formatDate } from "@/lib/format";
import { REFRESH_SECONDS } from "@/lib/config";

const formatAbsolute = (value: string | null) => {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("pl-PL", { timeZoneName: "short" });
  } catch {
    return value;
  }
};

export function MetaBar({ lastFetch, count }: { lastFetch: string | null; count: number }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const nextRefresh = lastFetch ? new Date(new Date(lastFetch).getTime() + REFRESH_SECONDS * 1000) : null;
  const lastFetchDisplay = mounted ? formatAbsolute(lastFetch) : "—";
  const nextRefreshDisplay = mounted ? formatAbsolute(nextRefresh ? nextRefresh.toISOString() : null) : "—";

  return (
    <div className="meta">
      <div>
        Ostatnie pobranie: <strong>{lastFetchDisplay}</strong>
        {mounted && lastFetch ? ` (${formatDate(lastFetch)})` : ""}
      </div>
      <div>
        Następne odświeżenie: <strong>{nextRefreshDisplay}</strong>
        {mounted && nextRefresh ? ` (${formatDate(nextRefresh.toISOString())})` : ""}
      </div>
      <div>
        Instrumenty: <strong>{count}</strong>
      </div>
    </div>
  );
}
