import { Analytics } from "@/lib/types";
import { formatNumber } from "@/lib/format";

export function StatCards({ analytics }: { analytics: Analytics }) {
  const { avg, min, max, std, last } = analytics;
  return (
    <div className="stat-cards">
      <div className="stat">
        <div className="label">Średnia</div>
        <div className="value value">{formatNumber(avg)}</div>
      </div>
      <div className="stat">
        <div className="label">Min</div>
        <div className="value value">{formatNumber(min)}</div>
      </div>
      <div className="stat">
        <div className="label">Max</div>
        <div className="value value">{formatNumber(max)}</div>
      </div>
      <div className="stat">
        <div className="label">Vol (std)</div>
        <div className="value value">{formatNumber(std)}</div>
      </div>
      <div className="stat">
        <div className="label">Ostatni</div>
        <div className="value value">{formatNumber(last)}</div>
      </div>
    </div>
  );
}
