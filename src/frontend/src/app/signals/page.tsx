import { SignalsTable } from "@/components/signals/SignalsTable";

export const metadata = { title: "Sygnały — Charon" };

export default function SignalsPage() {
  return (
    <div className="p-4 md:p-6 space-y-4">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Dziennik sygnałów</h1>
        <p className="text-muted-foreground text-sm mt-0.5">Ostatnie 100 sygnałów transakcyjnych wygenerowanych przez Charona</p>
      </div>
      <SignalsTable />
    </div>
  );
}
