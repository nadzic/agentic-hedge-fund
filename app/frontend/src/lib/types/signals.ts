export type SignalAnalyzeRequest = {
  query: string;
  symbol: string;
  horizon?: string;
};

export type SignalAnalyzeResponse = {
  symbol: string;
  signal: string;
  confidence: number;
  reasoning: string;
  warning?: string | null;
  error?: string | null;
};
