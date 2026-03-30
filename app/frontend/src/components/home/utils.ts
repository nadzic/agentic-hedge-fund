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
  const symbol = payload.symbol || "Unknown symbol";
  const signal = payload.signal.toLowerCase();
  const confidencePct = Math.round(payload.confidence * 100);
  const confidenceLabel = getConfidenceLabel(payload.confidence);
  const headline = getSignalHeadline(symbol, signal);
  const reasoning = payload.reasoning?.trim() || "No reasoning provided.";

  const lines = [
    headline,
    `Confidence: ${confidenceLabel} (${confidencePct}%)`,
    "",
    `Why: ${reasoning}`,
  ];

  const normalizedWarning = normalizeWarning(payload.warning);
  if (normalizedWarning) {
    lines.push("", `Note: ${normalizedWarning}`);
  }

  const nextStep = getNextStep(signal, normalizedWarning);
  if (nextStep) {
    lines.push("", `Next step: ${nextStep}`);
  }

  if (payload.error) {
    lines.push("", "Internal status: input validation needs more detail.");
  }

  return lines.join("\n");
}

function getSignalHeadline(symbol: string, signal: string): string {
  if (signal === "buy") return `${symbol} - Buy setup`;
  if (signal === "sell") return `${symbol} - Sell setup`;
  if (signal === "hold") return `${symbol} - Hold for now`;
  return `${symbol} - No trade right now`;
}

function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.75) return "High";
  if (confidence >= 0.6) return "Moderate";
  if (confidence >= 0.4) return "Low";
  return "Very low";
}

function normalizeWarning(warning: string | null): string | null {
  if (!warning) return null;

  if (warning.includes("Confidence clamped to min_confidence")) {
    return "Confidence is below the minimum trade threshold.";
  }

  if (warning.includes("Position size clamped to max_position_size")) {
    return "Suggested position size was reduced to stay within risk limits.";
  }

  return warning;
}

function getNextStep(signal: string, warning: string | null): string | null {
  if (signal === "buy") {
    return "Review entry and risk levels before placing any order.";
  }
  if (signal === "sell") {
    return "Confirm downside momentum and define your invalidation level.";
  }
  if (signal === "hold") {
    return "Wait for clearer direction before taking a new position.";
  }

  if (warning?.includes("minimum trade threshold")) {
    return "Wait for stronger confirmation or try a different time horizon.";
  }

  return "Provide more market context if you want a refined analysis.";
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
