import { NextRequest, NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";

function sanitizeNextPath(next: string | null): string {
  if (!next || !next.startsWith("/") || next.startsWith("//")) {
    return "/";
  }
  return next;
}

function getPublicOrigin(request: NextRequest): string {
  const configuredSiteUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (configuredSiteUrl) {
    try {
      return new URL(configuredSiteUrl).origin;
    } catch {
      // Fall through to forwarded headers when the configured URL is invalid.
    }
  }

  const forwardedProto = request.headers.get("x-forwarded-proto");
  const forwardedHost = request.headers.get("x-forwarded-host");
  if (forwardedProto && forwardedHost) {
    return `${forwardedProto}://${forwardedHost}`;
  }

  return request.nextUrl.origin;
}

function buildRedirectUrl(request: NextRequest, path: string, error?: string): URL {
  const url = new URL(path, getPublicOrigin(request));
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

  // Build an absolute URL from the current request host for Next.js proxy compatibility.
  return NextResponse.redirect(buildRedirectUrl(request, nextPath));
}
