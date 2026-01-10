import clsx from "clsx";
import { formatChange, formatNumber } from "@/lib/format";
import { Decision } from "@/lib/types";

const badgeClass = (code: string) => `badge ${code.toLowerCase()}`;

export function DecisionTable({ items }: { items: Decision[] }) {
  if (!items.length) {
    return (
      <div className="panel">
        <p className="muted">Brak danych do wyświetlenia.</p>
      </div>
    );
  }

  return (
    <div className="table-card">
      <table>
        <thead>
          <tr>
            <th>Instrument</th>
            <th>Kod</th>
            <th>Ostatni kurs</th>
            <th>Zmiana vs. średnia</th>
            <th>Decyzja</th>
            <th>Uzasadnienie</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.code}>
              <td>
                <span className={badgeClass(item.code)}>{item.code.slice(0, 3)}</span>
                {item.name}
              </td>
              <td className="muted">{item.code}</td>
              <td className="value">{formatNumber(item.latest_rate)}</td>
              <td className="value">{formatChange(item.change_pct)}</td>
              <td>
                <span className={clsx("pill", item.decision)}>{item.decision.toUpperCase()}</span>
              </td>
              <td className="muted">{item.basis}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
