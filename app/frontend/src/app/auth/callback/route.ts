import { NextRequest, NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";

function sanitizeNextPath(next: string | null): string {
  if (!next || !next.startsWith("/") || next.startsWith("//")) {
    return "/";
  }
  return next;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get("code");
  const nextPath = sanitizeNextPath(searchParams.get("next"));

  if (code) {
    const supabase = await createClient();
    await supabase.auth.exchangeCodeForSession(code);
  }

  // Relative redirect avoids leaking internal/proxy hosts (e.g. 0.0.0.0) into Location.
  return NextResponse.redirect(nextPath);
}
