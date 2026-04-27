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

export async function getAccessToken(): Promise<string | null> {
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

type ApiPostSseOptions = {
  signal?: AbortSignal;
  onEvent: (event: { event: string; data: unknown }) => void;
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

export async function apiPostSse(
  path: string,
  payload: unknown,
  options: ApiPostSseOptions,
): Promise<void> {
  const accessToken = await getAccessToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    credentials: "include",
    signal: options.signal,
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
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

  if (!response.body) {
    throw new Error("Streaming response body is not available.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const rawEvent of events) {
      const lines = rawEvent.split("\n");
      let eventName = "message";
      const dataLines: string[] = [];

      for (const line of lines) {
        if (line.startsWith("event:")) {
          eventName = line.slice("event:".length).trim() || "message";
          continue;
        }
        if (line.startsWith("data:")) {
          dataLines.push(line.slice("data:".length).trim());
        }
      }

      if (dataLines.length === 0) {
        continue;
      }

      const rawData = dataLines.join("\n");
      let parsedData: unknown = rawData;
      try {
        parsedData = JSON.parse(rawData) as unknown;
      } catch {
        parsedData = rawData;
      }
      options.onEvent({ event: eventName, data: parsedData });
    }
  }
}
