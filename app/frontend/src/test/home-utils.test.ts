import { describe, expect, it } from "vitest";

import {
  formatAssistantReply,
  getAnalyzeErrorMessage,
  getVisibleSuggestions,
  inferHorizon,
  inferSymbol,
  parseRateLimitError,
  parseTranscribeRateLimitError,
} from "../components/home/utils";

describe("home utils", () => {
  it("infers symbol from uppercase ticker and prefers last match", () => {
    expect(inferSymbol("Compare AAPL and NVDA for swing trading")).toBe("NVDA");
    expect(inferSymbol("please analyze tesla in detail")).toBeNull();
  });

  it("infers horizon from query keywords", () => {
    expect(inferHorizon("Need an intraday setup")).toBe("intraday");
    expect(inferHorizon("This is for position trade")).toBe("position");
    expect(inferHorizon("Looking for a swing entry")).toBe("swing");
    expect(inferHorizon("Analyze this idea")).toBeNull();
  });

  it("formats assistant reply with warning normalization and next step", () => {
    const reply = formatAssistantReply({
      symbol: "NVDA",
      signal: "buy",
      confidence: 0.74,
      reasoning: "Momentum and earnings revisions look supportive.",
      warning: "Confidence clamped to min_confidence",
      error: null,
    });

    expect(reply).toContain("NVDA - Buy setup");
    expect(reply).toContain("Confidence: Moderate (74%)");
    expect(reply).toContain("Note: Confidence is below the minimum trade threshold.");
    expect(reply).toContain("Next step: Review entry and risk levels before placing any order.");
  });

  it("returns useful defaults for rate-limit payload parsing", () => {
    const parsed = parseRateLimitError({ detail: {} });
    expect(parsed.message).toBe("Free limit reached (2/day). Sign in or sign up to continue.");
    expect(parsed.resetAt).toBeNull();
    expect(parsed.upgradeRequired).toBe(false);
  });

  it("keeps invalid reset_at string unchanged in transcribe rate-limit parsing", () => {
    const parsed = parseTranscribeRateLimitError({
      detail: {
        message: "Voice limit reached",
        reset_at: "not-a-real-date",
      },
    });
    expect(parsed.message).toBe("Voice limit reached");
    expect(parsed.resetAt).toBe("not-a-real-date");
  });

  it("returns suggestions filtered by input and limited to max five", () => {
    const suggestions = getVisibleSuggestions("aapl");
    expect(suggestions.length).toBeLessThanOrEqual(5);
    expect(suggestions[0]).toContain("AAPL");
  });

  it("formats timeout and generic errors", () => {
    const timeoutMessage = getAnalyzeErrorMessage(
      new DOMException("The operation was aborted", "AbortError"),
      45_000,
    );
    expect(timeoutMessage).toBe("Request timed out after 45s");

    expect(getAnalyzeErrorMessage(new Error("boom"), 30_000)).toBe("boom");
    expect(getAnalyzeErrorMessage("bad", 30_000)).toBe("Unknown error");
  });
});
