import Link from "next/link";

import { apiBase, fetchJson } from "../lib/api";

interface Instrument {
  code: string;
  name: string;
  type: string;
  enabled: boolean;
}

interface Quote {
  code: string;
  effective_date: string;
  mid: number | null;
  bid: number | null;
  ask: number | null;
}

interface Signal {
  code: string;
  as_of_date: string;
  signal: string;
  confidence: number;
  explain_summary: string;
}

interface Status {
  last_run: string | null;
  last_effective_date: string | null;
  next_run_at: string | null;
  service_time: string;
  version: string;
}

function badgeColor(signal: string) {
  if (signal === "BUY") return "bg-emerald-500/20 text-emerald-300";
  if (signal === "SELL") return "bg-rose-500/20 text-rose-300";
  return "bg-slate-500/20 text-slate-200";
}

export default async function HomePage() {
  const [status, instruments, quotes, signals] = await Promise.all([
    fetchJson<Status>("/api/status"),
    fetchJson<Instrument[]>("/api/instruments"),
    fetchJson<Quote[]>("/api/quotes/latest"),
    fetchJson<Signal[]>("/api/signals/latest"),
  ]);

  const quoteMap = new Map(quotes.map((quote) => [quote.code, quote]));
  const signalMap = new Map(signals.map((signal) => [signal.code, signal]));

  return (
    <main>
      <section className="mb-6 rounded-lg border border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-300">
        <div className="flex flex-wrap gap-6">
          <div>
            <p className="uppercase text-xs text-slate-400">Last update</p>
            <p>{status.last_run ?? "n/a"}</p>
          </div>
          <div>
            <p className="uppercase text-xs text-slate-400">Next scheduled</p>
            <p>{status.next_run_at ?? "n/a"}</p>
          </div>
          <div>
            <p className="uppercase text-xs text-slate-400">Service time</p>
            <p>{status.service_time}</p>
          </div>
          <div>
            <p className="uppercase text-xs text-slate-400">API</p>
            <p>{apiBase}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        {instruments.map((instrument) => {
          const quote = quoteMap.get(instrument.code);
          const signal = signalMap.get(instrument.code);
          const disabled = instrument.code === "XAG" && !instrument.enabled;

          return (
            <div key={instrument.code} className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold">{instrument.code}</h2>
                  <p className="text-sm text-slate-400">{instrument.name}</p>
                </div>
                {disabled ? (
                  <span className="rounded-full bg-slate-700/50 px-3 py-1 text-xs text-slate-300">Disabled</span>
                ) : (
                  <span className={`rounded-full px-3 py-1 text-xs ${badgeColor(signal?.signal ?? "HOLD")}`}>
                    {signal?.signal ?? "HOLD"}
                  </span>
                )}
              </div>
              <div className="mt-3 text-sm">
                {disabled ? (
                  <p className="text-slate-400">Silver provider disabled.</p>
                ) : (
                  <>
                    <p>Rate: {quote?.mid ?? quote?.bid ?? quote?.ask ?? "n/a"}</p>
                    <p className="text-slate-400">Confidence: {signal?.confidence ?? "n/a"}</p>
                    <p className="text-slate-500">{signal?.explain_summary}</p>
                  </>
                )}
              </div>
              <div className="mt-4">
                <Link className="text-sm text-amber-300 hover:text-amber-200" href={`/instrument/${instrument.code}`}>
                  View details →
                </Link>
              </div>
            </div>
          );
        })}
      </section>
    </main>
  );
}
