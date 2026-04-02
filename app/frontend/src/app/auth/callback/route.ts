import { NextRequest, NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";

function sanitizeNextPath(next: string | null): string {
  if (!next || !next.startsWith("/") || next.startsWith("//")) {
    return "/";
  }
  return next;
}

function buildRedirectUrl(request: NextRequest, path: string, error?: string): URL {
  const url = new URL(path, request.url);
  if (error) {
    url.searchParams.set("error", error);
  }
  return url;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get("code");
  const nextPath = sanitizeNextPath(searchParams.get("next"));

  if (!code) {
    return NextResponse.redirect(buildRedirectUrl(request, "/sign-in", "missing_auth_code"));
  }

  try {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) {
      return NextResponse.redirect(buildRedirectUrl(request, "/sign-in", "auth_callback_failed"));
    }
  } catch {
    return NextResponse.redirect(buildRedirectUrl(request, "/sign-in", "auth_callback_failed"));
  }

  // Relative redirect avoids leaking internal/proxy hosts (e.g. 0.0.0.0) into Location.
  return NextResponse.redirect(nextPath);
}
