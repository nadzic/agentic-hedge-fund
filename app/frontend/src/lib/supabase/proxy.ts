import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

function isLikelySupabasePublicKey(value: string): boolean {
  return value.startsWith("sb_publishable_") || value.split(".").length === 3;
}

export async function updateSession(request: NextRequest) {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  const isConfigured = Boolean(supabaseUrl && supabaseAnonKey);
  const hasValidKey = Boolean(supabaseAnonKey && isLikelySupabasePublicKey(supabaseAnonKey));
  if (!isConfigured || !hasValidKey) {
    // Keep app available even when auth env is missing/invalid.
    return NextResponse.next({
      request,
    });
  }

  let response = NextResponse.next({
    request,
  });
  const resolvedSupabaseUrl = supabaseUrl as string;
  const resolvedSupabaseAnonKey = supabaseAnonKey as string;

  const supabase = createServerClient(resolvedSupabaseUrl, resolvedSupabaseAnonKey, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        for (const { name, value } of cookiesToSet) {
          request.cookies.set(name, value);
        }

        response = NextResponse.next({
          request,
        });

        for (const { name, value, options } of cookiesToSet) {
          response.cookies.set(name, value, options);
        }
      },
    },
  });

  try {
    await supabase.auth.getUser();
  } catch {
    // Do not block page rendering if auth refresh fails.
  }

  return response;
}
