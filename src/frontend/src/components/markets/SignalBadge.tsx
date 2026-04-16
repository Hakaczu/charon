import { cn } from "@/lib/utils";
import type { SignalType } from "@/types/api";

const MAP = {
  BUY: { label: "BUY", cls: "bg-green-500/15 text-green-500 border-green-500/30" },
  SELL: { label: "SELL", cls: "bg-red-500/15 text-red-500 border-red-500/30" },
  HOLD: { label: "HOLD", cls: "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 border-yellow-500/30" },
  NEUTRAL: { label: "—", cls: "bg-muted text-muted-foreground border-border" },
  WAIT: { label: "—", cls: "bg-muted text-muted-foreground border-border" },
} as const;

interface Props {
  signal: SignalType | "NEUTRAL" | "WAIT" | string;
  size?: "sm" | "md";
  pulse?: boolean;
}

export function SignalBadge({ signal, size = "sm", pulse = false }: Props) {
  const key = signal in MAP ? signal as keyof typeof MAP : "NEUTRAL";
  const { label, cls } = MAP[key];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-semibold tracking-wide",
        size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        cls
      )}
    >
      {pulse && (signal === "BUY" || signal === "SELL") && (
        <span
          className={cn(
            "inline-block h-1.5 w-1.5 rounded-full animate-pulse",
            signal === "BUY" ? "bg-green-500" : "bg-red-500"
          )}
        />
      )}
      {label}
    </span>
  );
}
