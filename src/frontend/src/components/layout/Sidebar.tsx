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
  ChevronLeft,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { useSidebar } from "@/providers/SidebarProvider";

const ITEMS = [
  { href: "/markets", label: "Markets", Icon: BarChart2 },
  { href: "/signals", label: "Signals", Icon: Bell },
  { href: "/miner", label: "Miner", Icon: Activity },
  { href: "/backtesting", label: "Backtest", Icon: FlaskConical },
  { href: "/analysis", label: "Analysis", Icon: BrainCircuit },
  { href: "/finances", label: "Finances", Icon: Wallet },
];

export function Sidebar() {
  const pathname = usePathname();
  const { collapsed, toggle } = useSidebar();

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col fixed inset-y-0 left-0 z-40 border-r border-border bg-background transition-all duration-200",
        collapsed ? "w-14" : "w-56"
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          "flex items-center gap-2 px-3 h-14 border-b border-border",
          collapsed && "justify-center"
        )}
      >
        <TrendingUp size={22} className="text-primary shrink-0" />
        {!collapsed && (
          <span className="font-bold text-base tracking-tight truncate">Charon</span>
        )}
      </div>

      {/* Nav items */}
      <nav className="flex flex-col gap-1 p-2 flex-1">
        {ITEMS.map(({ href, label, Icon }) => {
          const active = pathname.startsWith(href);
          const item = (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-2.5 py-2 text-sm font-medium transition-colors",
                collapsed && "justify-center px-0",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon size={18} strokeWidth={active ? 2.5 : 1.75} className="shrink-0" />
              {!collapsed && <span className="truncate">{label}</span>}
            </Link>
          );

          if (collapsed) {
            return (
              <Tooltip key={href}>
                <TooltipTrigger>
                  {item}
                </TooltipTrigger>
                <TooltipContent side="right">{label}</TooltipContent>
              </Tooltip>
            );
          }
          return item;
        })}
      </nav>

      {/* Bottom controls */}
      <div
        className={cn(
          "p-2 border-t border-border flex items-center",
          collapsed ? "justify-center flex-col gap-2" : "justify-between"
        )}
      >
        <ThemeToggle />
        <button
          onClick={toggle}
          className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          aria-label="Toggle sidebar"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  );
}
