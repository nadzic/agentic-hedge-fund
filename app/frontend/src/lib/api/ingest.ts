import { apiPost } from "@/lib/api/client";
import type { RagIngestRequest, RagIngestResponse } from "@/lib/types/rag";

export function ingestAndIndex(payload: RagIngestRequest): Promise<RagIngestResponse> {
  return apiPost<RagIngestResponse>("/rag/ingest-index", payload);
}
