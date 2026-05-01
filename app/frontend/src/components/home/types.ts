export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export type Brief = {
  executive_summary: string | null;
  what_changed: string[];
  what_matters_most_now: string[];
  bull_points: string[];
  bear_points: string[];
  what_to_watch_next: string[];
};

export type EvidenceQualitySummary = {
  strong: number;
  medium: number;
  weak: number;
};

export type ResearchResponse = {
  company: string | null;
  ticker: string | null;
  brief: Brief;
  evidence_quality_summary: EvidenceQualitySummary;
  sources: Array<Record<string, unknown>>;
  selected_evidence: Array<Record<string, unknown>>;
  discarded_evidence_count: number;
  disclaimer: string;
  warning: string | null;
  error: string | null;
};

export type TranscriptionResponse = {
  text: string;
};

export type ModelInfoResponse = {
  model: string;
};
