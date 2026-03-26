import { apiPost } from "@/lib/api/client";
import type { RagQueryRequest, RagQueryResponse } from "@/lib/types/rag";

export function queryRag(payload: RagQueryRequest): Promise<RagQueryResponse> {
  return apiPost<RagQueryResponse>("/rag/query", payload);
}
