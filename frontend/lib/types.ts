export type Decision = {
  name: string;
  code: string;
  latest_rate: number;
  change_pct: number | null;
  decision: "buy" | "sell" | "hold" | string;
  basis: string;
  icon_class?: string;
};

export type RawSnapshot = {
  items: Decision[];
  history_map: Record<string, [string, number][]>;
  last_fetch: string | null;
};

export type HistoryPoint = {
  date: string;
  value: number;
};

export type Snapshot = {
  items: Decision[];
  history: Record<string, HistoryPoint[]>;
  lastFetch: string | null;
};

export type Analytics = {
  avg: number | null;
  min: number | null;
  max: number | null;
  std: number | null;
  last: number | null;
  lastDate: string | null;
};
