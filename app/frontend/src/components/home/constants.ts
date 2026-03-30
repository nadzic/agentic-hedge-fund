export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const ANALYZE_TIMEOUT_MS = 45_000;

export const MODEL_OPTIONS = [
  {
    id: "opus-4.6",
    label: "Opus 4.6",
    detail: "Deeper reasoning",
  },
  {
    id: "chat-gpt-5.4",
    label: "ChatGPT 5.4",
    detail: "Faster responses",
  },
] as const;

export type ModelOptionId = (typeof MODEL_OPTIONS)[number]["id"];

export const SUGGESTED_PROMPTS = [
  "Please analyze NVDA for swing trading",
  "Please analyze AAPL for swing trading",
  "Please analyze TSLA for swing trading",
] as const;
