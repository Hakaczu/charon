"use client";

import { useMemo, useState } from "react";
import { DecisionTable } from "./DecisionTable";
import { RateChart } from "./RateChart";
import { StatCards } from "./StatCards";
import { MetaBar } from "./MetaBar";
import { computeAnalyticsMap } from "@/lib/metrics";
import { Snapshot } from "@/lib/types";

export function Dashboard({ snapshot }: { snapshot: Snapshot }) {
  const { items, history, lastFetch } = snapshot;
  const codesWithHistory = items.filter((i) => history[i.code]?.length).map((i) => i.code);
  const [selected, setSelected] = useState<string>(codesWithHistory[0] || items[0]?.code || "");

  const analyticsMap = useMemo(() => computeAnalyticsMap(history), [history]);
  const selectedHistory = history[selected] || [];
  const selectedAnalytics = analyticsMap[selected] || {
    avg: null,
    min: null,
    max: null,
    std: null,
    last: null,
    lastDate: null,
  };

  return (
    <div className="container">
      <h1>Charon • Kursy NBP</h1>
      <p className="subtitle">
        Bieżące i historyczne kursy ( {items.length} instrumentów ) + rekomendacja kup/sprzedaj/hold oparta na odchyleniu od średniej.
      </p>

      <MetaBar lastFetch={lastFetch} count={items.length} />

      <div className="panel">
        <h3>
          <i className="fa-solid fa-chart-line" /> Wykres historyczny
        </h3>
        <div className="controls">
          <label htmlFor="instrumentSelect" className="muted">
            Instrument:
          </label>
          <select id="instrumentSelect" value={selected} onChange={(e) => setSelected(e.target.value)}>
            {(codesWithHistory.length ? codesWithHistory : items.map((i) => i.code)).map((code) => (
              <option key={code} value={code}>
                {code}
              </option>
            ))}
          </select>
        </div>
        <div className="grid-two">
          <div>
            {selected ? <RateChart code={selected} series={selectedHistory} /> : <div className="muted">Brak danych do wykresu.</div>}
          </div>
          <StatCards analytics={selectedAnalytics} />
        </div>
      </div>

      <DecisionTable items={items} />
    </div>
  );
}
