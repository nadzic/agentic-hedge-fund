import { createClient as createSupabaseClient } from "@/lib/supabase/client";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

async function getAccessToken(): Promise<string | null> {
  try {
    const supabase = createSupabaseClient();
    const { data, error } = await supabase.auth.getSession();
    if (error) throw new Error(`Session error: ${error.message}`);
    return data.session?.access_token ?? null;
  } catch {
    return null;
  }
}

type ApiPostOptions = {
  signal?: AbortSignal;
};

export async function apiPost<TResponse>(
  path: string,
  payload: unknown,
  options?: ApiPostOptions,
): Promise<TResponse> {
  const accessToken = await getAccessToken();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    credentials: "include",
    signal: options?.signal,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let parsedPayload: unknown = null;
    const text = await response.text();
    try {
      parsedPayload = text ? (JSON.parse(text) as unknown) : null;
    } catch {
      parsedPayload = text;
    }
    throw new ApiError(`API error ${response.status}: ${text}`, response.status, parsedPayload);
  }

  return (await response.json()) as TResponse;
}
