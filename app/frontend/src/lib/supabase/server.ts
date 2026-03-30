import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

function isLikelySupabasePublicKey(value: string): boolean {
  return value.startsWith("sb_publishable_") || value.split(".").length === 3;
}

export async function createClient() {
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

  const cookieStore = await cookies();
  return createServerClient(supabaseUrl, supabaseAnonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        for (const { name, value, options } of cookiesToSet) {
          cookieStore.set(name, value, options);
        }
      },
    },
  });
}
