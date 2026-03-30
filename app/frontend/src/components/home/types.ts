export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export type AnalyzeResponse = {
  symbol: string;
  signal: string;
  confidence: number;
  reasoning: string;
  warning: string | null;
  error: string | null;
};

export type TranscriptionResponse = {
  text: string;
};

export type ModelInfoResponse = {
  model: string;
};

export type Horizon = "intraday" | "swing" | "position";
