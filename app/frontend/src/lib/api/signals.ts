import { apiPost } from "@/lib/api/client";
import type {
  SignalAnalyzeRequest,
  SignalAnalyzeResponse,
} from "@/lib/types/signals";

export function analyzeSignal(
  payload: SignalAnalyzeRequest,
): Promise<SignalAnalyzeResponse> {
  return apiPost<SignalAnalyzeResponse>("/signals/analyze", payload);
}
