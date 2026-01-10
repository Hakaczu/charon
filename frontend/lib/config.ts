const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export const API_BASE = apiBase.replace(/\/$/, "");
export const REFRESH_SECONDS = Number(process.env.NEXT_PUBLIC_REFRESH_SECONDS || "3600");
