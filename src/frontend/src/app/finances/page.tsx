import { Wallet } from "lucide-react";

export const metadata = { title: "Finances — Charon" };

export default function FinancesPage() {
  return (
    <div className="p-4 md:p-6 flex flex-col items-center justify-center min-h-[60vh] gap-4 text-center">
      <div className="rounded-full bg-muted p-6">
        <Wallet size={36} className="text-muted-foreground" />
      </div>
      <h1 className="text-2xl font-bold">Finances</h1>
      <p className="text-muted-foreground max-w-sm">
        This section is under construction. Financial portfolio tracking and reporting coming soon.
      </p>
    </div>
  );
}
