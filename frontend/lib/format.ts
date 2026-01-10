import { formatDistanceToNow, parseISO } from "date-fns";
import { pl } from "date-fns/locale";

export const formatNumber = (value: number | null | undefined, digits = 4) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toFixed(digits);
};

export const formatChange = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toFixed(2)}%`;
};

export const formatDate = (value: string | null) => {
  if (!value) return "—";
  try {
    return formatDistanceToNow(parseISO(value), { addSuffix: true, locale: pl });
  } catch (e) {
    return value;
  }
};
