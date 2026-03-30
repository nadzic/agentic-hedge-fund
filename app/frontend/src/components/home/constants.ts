export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const ANALYZE_TIMEOUT_MS = 45_000;
export const DICTATION_MAX_DURATION_MS = 15_000;

export const SUGGESTED_PROMPTS = [
  "Please analyze NVDA for swing trading",
  "Please analyze AAPL for intraday trading",
  "Please analyze TSLA for position trading",
] as const;
