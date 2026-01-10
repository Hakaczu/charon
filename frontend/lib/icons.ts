const ICONS: Record<string, string> = {
  USD: "🇺🇸",
  EUR: "🇪🇺",
  JPY: "🇯🇵",
  GBP: "🇬🇧",
  AUD: "🇦🇺",
  CAD: "🇨🇦",
  CHF: "🇨🇭",
  CNY: "🇨🇳",
  SEK: "🇸🇪",
  NZD: "🇳🇿",
  NOK: "🇳🇴",
  XAU: "🥇",
};

export function getCurrencyIcon(code: string): string {
  return ICONS[code.toUpperCase()] ?? "🪙";
}