import { createClient as createSupabaseClient } from "@/lib/supabase/client";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function getAccessToken(): Promise<string | null> {
  const supabase = createSupabaseClient();
  const { data, error } = await supabase.auth.getSession();
  if (error) throw new Error(`Session error: ${error.message}`);
  return data.session?.access_token ?? null;
}

export async function apiPost<TResponse>(
  path: string,
  payload: unknown,
): Promise<TResponse> {
  const accessToken = await getAccessToken();


  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API error ${response.status}: ${text}`);
  }

  return (await response.json()) as TResponse;
}
