import Link from "next/link";

import { fetchJson } from "../../../lib/api";

interface QuotePoint {
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
  explain_json: Record<string, unknown>;
  disclaimer: string;
}

export default async function InstrumentPage({ params }: { params: { code: string } }) {
  const code = params.code.toUpperCase();
  const [history, signal] = await Promise.all([
    fetchJson<QuotePoint[]>(`/api/quotes/${code}/history?days=90`),
    fetchJson<Signal[]>(`/api/signals/latest?codes=${code}`),
  ]);

  const latest = history[history.length - 1];
  const activeSignal = signal[0];

  return (
    <main>
      <Link className="text-sm text-amber-300 hover:text-amber-200" href="/">
        ← Back
      </Link>
      <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
        <h2 className="text-2xl font-semibold">{code}</h2>
        <p className="text-slate-400">Latest: {latest?.mid ?? latest?.bid ?? latest?.ask ?? "n/a"}</p>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
          <h3 className="text-lg font-semibold">Recent history</h3>
          <div className="mt-2 space-y-1 text-sm text-slate-300">
            {history.slice(-10).map((row) => (
              <div key={row.effective_date} className="flex justify-between">
                <span>{row.effective_date}</span>
                <span>{row.mid ?? row.bid ?? row.ask}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
          <h3 className="text-lg font-semibold">Signal</h3>
          {activeSignal ? (
            <div className="mt-2 text-sm text-slate-300">
              <p>
                <strong>{activeSignal.signal}</strong> ({activeSignal.confidence})
              </p>
              <p className="text-slate-400">{activeSignal.explain_summary}</p>
              <p className="mt-2 text-xs text-slate-500">{activeSignal.disclaimer}</p>
            </div>
          ) : (
            <p className="mt-2 text-sm text-slate-400">No signal available.</p>
          )}
        </div>
      </div>
    </main>
  );
}
