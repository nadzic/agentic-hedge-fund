import { SUGGESTED_PROMPTS } from "@/components/home/constants";
import { AnalyzeResponse, Horizon } from "@/components/home/types";

export function inferSymbol(query: string): string | null {
  const candidates = query.match(/\b[A-Z]{1,5}\b/g);
  return candidates?.at(-1) ?? null;
}

export function inferHorizon(query: string): Horizon | null {
  const normalized = query.toLowerCase();
  if (normalized.includes("intraday")) return "intraday";
  if (normalized.includes("position")) return "position";
  if (normalized.includes("swing")) return "swing";
  return null;
}

export function formatAssistantReply(payload: AnalyzeResponse): string {
  const lines = [
    `Symbol: ${payload.symbol}`,
    `Signal: ${payload.signal.toUpperCase()}`,
    `Confidence: ${(payload.confidence * 100).toFixed(1)}%`,
    "",
    payload.reasoning,
  ];
  if (payload.warning) {
    lines.push("", `Warning: ${payload.warning}`);
  }
  if (payload.error) {
    lines.push("", `Error: ${payload.error}`);
  }
  return lines.join("\n");
}

export function getVisibleSuggestions(input: string): string[] {
  const query = input.trim().toLowerCase();
  if (!query) {
    return SUGGESTED_PROMPTS.slice(0, 5);
  }
  return SUGGESTED_PROMPTS.filter((prompt) => prompt.toLowerCase().includes(query)).slice(0, 5);
}

export function getAnalyzeErrorMessage(error: unknown, timeoutMs: number): string {
  if (error instanceof DOMException && error.name === "AbortError") {
    return `Request timed out after ${Math.round(timeoutMs / 1000)}s`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unknown error";
}
