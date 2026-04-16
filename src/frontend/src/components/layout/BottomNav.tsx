"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart2,
  Bell,
  Activity,
  FlaskConical,
  BrainCircuit,
  Wallet,
} from "lucide-react";
import { cn } from "@/lib/utils";

const ITEMS = [
  { href: "/markets", label: "Rynki", Icon: BarChart2 },
  { href: "/signals", label: "Sygnały", Icon: Bell },
  { href: "/miner", label: "Miner", Icon: Activity },
  { href: "/backtesting", label: "Backtest", Icon: FlaskConical },
  { href: "/analysis", label: "Analiza", Icon: BrainCircuit },
  { href: "/finances", label: "Finanse", Icon: Wallet },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 flex h-16 items-center justify-around border-t border-border bg-background/95 backdrop-blur-sm md:hidden">
      {ITEMS.map(({ href, label, Icon }) => {
        const active = pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-col items-center gap-0.5 px-2 py-1 text-[10px] font-medium transition-colors",
              active ? "text-primary" : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Icon
              size={20}
              className={cn(active && "text-primary")}
              strokeWidth={active ? 2.5 : 1.75}
            />
            <span>{label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
