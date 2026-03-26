export type RagQueryRequest = {
  query: string;
  symbol: string;
  horizon?: string;
  top_k?: number;
  sparse_top_k?: number;
  alpha?: number;
  max_context_chunks?: number;
};

export type RagQueryResponse = {
  answer: string;
  confidence: number | null;
  citations: string[];
  reasoning: string | null;
};

export type RagIngestRequest = {
  pdf_paths?: string[];
  pdf_recursive?: boolean;
  urls?: string[];
  min_chars?: number;
  snapshot_path?: string;
  collection_name?: string;
};

export type RagIngestResponse = {
  input_count: number;
  transformed_count: number;
  dropped_empty_or_short: number;
  dropped_challenge_or_junk: number;
  indexed_count: number;
  snapshot_path: string;
  collection_name: string;
};
