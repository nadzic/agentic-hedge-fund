import { createBrowserClient } from "@supabase/ssr";

function isLikelySupabasePublicKey(value: string): boolean {
  return value.startsWith("sb_publishable_") || value.split(".").length === 3;
}

export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Missing Supabase configuration. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.",
    );
  }

  if (!isLikelySupabasePublicKey(supabaseAnonKey)) {
    throw new Error(
      "Invalid NEXT_PUBLIC_SUPABASE_ANON_KEY format. Use the Supabase anon/publishable key (not project ref).",
    );
  }

  return createBrowserClient(supabaseUrl, supabaseAnonKey);
}
