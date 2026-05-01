import { describe, expect, it } from "vitest";

import {
  formatResearchReply,
  getAnalyzeErrorMessage,
  getVisibleSuggestions,
} from "../components/home/utils";
import { ResearchResponse } from "../components/home/types";

describe("home utils", () => {
  it("formats research response into plain text brief", () => {
    const reply = formatResearchReply({
      company: "NVIDIA Corporation",
      ticker: "NVDA",
      brief: {
        executive_summary: "Revenue grew and guidance improved.",
        what_changed: ["Revenue up YoY"],
        what_matters_most_now: ["Data center demand remains strong"],
        bull_points: ["Strong AI demand"],
        bear_points: ["Gross margin pressure risk"],
        what_to_watch_next: ["Next-quarter guidance"],
      },
      evidence_quality_summary: { strong: 4, medium: 3, weak: 1 },
      sources: [
        { title: "Official earnings release", source_type: "earnings_release", final_source_score: 0.95 },
      ],
      selected_evidence: [],
      discarded_evidence_count: 3,
      disclaimer: "This is not investment advice.",
      warning: null,
      error: null,
    } satisfies ResearchResponse);

    expect(reply).toContain("NVIDIA Corporation (NVDA)");
    expect(reply).toContain("Latest reporting research brief");
    expect(reply).toContain("Executive summary");
    expect(reply).toContain("Evidence quality");
    expect(reply).toContain("Strong: 4 | Medium: 3 | Weak: 1");
    expect(reply).toContain("Disclaimer");
  });

  it("returns suggestions filtered by input and limited to max five", () => {
    const suggestions = getVisibleSuggestions("research nvda");
    expect(suggestions.length).toBeLessThanOrEqual(5);
    expect(suggestions[0]).toContain("NVDA");
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
