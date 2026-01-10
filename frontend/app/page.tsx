import { Dashboard } from "@/components/Dashboard";
import { fetchSnapshot } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Page() {
  try {
    const snapshot = await fetchSnapshot();
    return <Dashboard snapshot={snapshot} />;
  } catch (error) {
    return (
      <div className="container">
        <h1>Charon • Kursy NBP</h1>
        <p className="subtitle">Nie udało się pobrać danych z API.</p>
        <pre className="panel" style={{ overflow: "auto" }}>
          {String(error)}
        </pre>
      </div>
    );
  }
}
