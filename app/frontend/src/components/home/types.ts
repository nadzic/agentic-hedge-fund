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

export type DictationResult = {
  transcript: string;
};

export type DictationResultList = {
  length: number;
  item(index: number): DictationResult | null;
  [index: number]: DictationResult;
};

export type DictationEvent = {
  resultIndex: number;
  results: DictationResultList;
};

export type DictationRecognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: DictationEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

export type DictationConstructor = new () => DictationRecognition;

export type Horizon = "intraday" | "swing" | "position";
