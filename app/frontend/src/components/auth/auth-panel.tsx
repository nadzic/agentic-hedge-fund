"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { createClient } from "@/lib/supabase/client";

type AuthVariant = "sign-in" | "sign-up";

type AuthPanelProps = {
  variant: AuthVariant;
};

function getAuthErrorMessage(errorCode: string | null): string | null {
  if (!errorCode) return null;

  switch (errorCode) {
    case "missing_auth_code":
      return "Authentication could not be completed. Please try again.";
    case "auth_callback_failed":
      return "Sign-in failed during callback. Please try again.";
    default:
      return "Authentication failed. Please try again.";
  }
}

function resolveAuthRedirectBase(): string {
  const configuredSiteUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (configuredSiteUrl) {
    try {
      const configuredUrl = new URL(configuredSiteUrl);
      return `${configuredUrl.protocol}//${configuredUrl.host}`;
    } catch {
      // Ignore invalid configured site URL and fall back to window location.
    }
  }

  const { protocol, hostname, port } = window.location;
  const isLocalHost =
    hostname === "localhost" || hostname === "127.0.0.1" || hostname === "0.0.0.0";
  const resolvedHostname = hostname === "0.0.0.0" ? "localhost" : hostname;
  const resolvedProtocol = isLocalHost ? "http:" : protocol;
  const resolvedPort = port ? `:${port}` : "";

  return `${resolvedProtocol}//${resolvedHostname}${resolvedPort}`;
}

const panelContent = {
  "sign-in": {
    title: "Log into your account",
    primary: "Login with Google",
    secondary: "Login with email",
    footerText: "Don't have an account?",
    footerAction: "Sign up",
    footerHref: "/sign-up",
  },
  "sign-up": {
    title: "Create your account",
    primary: "Sign up with Google",
    secondary: "Sign up with email",
    footerText: "Already have an account?",
    footerAction: "Sign in",
    footerHref: "/sign-in",
  },
} as const;

export function AuthPanel({ variant }: AuthPanelProps) {
  const router = useRouter();
  const content = panelContent[variant];
  const isSignIn = variant === "sign-in";
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(() => {
    if (typeof window === "undefined") {
      return null;
    }
    const params = new URLSearchParams(window.location.search);
    return getAuthErrorMessage(params.get("error"));
  });
  const [authAction, setAuthAction] = useState<"google" | "email" | null>(null);

  async function handleGoogleAuth() {
    setIsBusy(true);
    setAuthAction("google");
    setMessage(null);
    let supabase;
    try {
      supabase = createClient();
    } catch (error) {
      const text = error instanceof Error ? error.message : "Invalid Supabase configuration.";
      setMessage(text);
      setIsBusy(false);
      setAuthAction(null);
      return;
    }
    const redirectTo = `${resolveAuthRedirectBase()}/auth/callback?next=/`;
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo },
    });
    if (error) {
      setMessage(error.message);
      setIsBusy(false);
      setAuthAction(null);
    }
  }

  async function handleEmailAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsBusy(true);
    setAuthAction("email");
    setMessage(null);

    if (isSignIn) {
      let supabase;
      try {
        supabase = createClient();
      } catch (error) {
        const text = error instanceof Error ? error.message : "Invalid Supabase configuration.";
        setMessage(text);
        setIsBusy(false);
        setAuthAction(null);
        return;
      }
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) {
        setMessage(error.message);
      } else {
        router.push("/");
        router.refresh();
      }
      setIsBusy(false);
      setAuthAction(null);
      return;
    }

    const emailRedirectTo = `${resolveAuthRedirectBase()}/auth/callback?next=/`;
    let supabase;
    try {
      supabase = createClient();
    } catch (error) {
      const text = error instanceof Error ? error.message : "Invalid Supabase configuration.";
      setMessage(text);
      setIsBusy(false);
      setAuthAction(null);
      return;
    }
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { emailRedirectTo },
    });
    if (error) {
      setMessage(error.message);
    } else {
      setMessage("Check your email to confirm your account.");
    }
    setIsBusy(false);
    setAuthAction(null);
  }

  return (
    <section className="relative z-10 flex w-full max-w-xl flex-col justify-between bg-black/45 px-8 py-8 backdrop-blur-sm md:px-12">
      <div>
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm font-semibold tracking-wide text-zinc-300 transition hover:text-white"
        >
          <span className="text-base">V</span>
          <span>VERITAKE</span>
        </Link>
      </div>

      <div className="mx-auto w-full max-w-sm space-y-4">
        <h1 className="text-3xl font-semibold tracking-tight text-white">{content.title}</h1>

        <button
          type="button"
          onClick={handleGoogleAuth}
          disabled={isBusy}
          className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-white px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isBusy && authAction === "google" ? (
            <>
              <span
                aria-hidden
                className="h-4 w-4 animate-spin rounded-full border-2 border-black/25 border-t-black"
              />
              Redirecting...
            </>
          ) : (
            <>
              <svg aria-hidden viewBox="0 0 24 24" className="h-4 w-4">
                <path
                  fill="#EA4335"
                  d="M12 10.2v3.9h5.4c-.24 1.26-.96 2.34-2.04 3.06l3.3 2.55c1.92-1.77 3.03-4.38 3.03-7.5 0-.72-.06-1.41-.18-2.07H12z"
                />
                <path
                  fill="#34A853"
                  d="M12 22c2.7 0 4.97-.9 6.63-2.43l-3.3-2.55c-.9.6-2.07.96-3.33.96-2.55 0-4.71-1.71-5.49-4.02l-3.42 2.64C4.74 19.89 8.1 22 12 22z"
                />
                <path
                  fill="#4A90E2"
                  d="M6.51 13.96A5.97 5.97 0 0 1 6.2 12c0-.69.12-1.35.3-1.96L3.09 7.4A9.9 9.9 0 0 0 2 12c0 1.59.39 3.09 1.09 4.4l3.42-2.64z"
                />
                <path
                  fill="#FBBC05"
                  d="M12 6.02c1.47 0 2.79.51 3.84 1.5l2.88-2.88C16.97 2.98 14.7 2 12 2 8.1 2 4.74 4.11 3.09 7.4l3.42 2.64c.78-2.31 2.94-4.02 5.49-4.02z"
                />
              </svg>
              {content.primary}
            </>
          )}
        </button>

        <div className="relative py-1">
          <div className="h-px w-full bg-zinc-800" />
        </div>

        <button
          type="button"
          onClick={() => setShowEmailForm((prev) => !prev)}
          disabled={isBusy}
          className="w-full rounded-full border border-zinc-700 bg-transparent px-4 py-2.5 text-sm font-medium text-zinc-200 transition hover:border-zinc-500 hover:text-white"
        >
          {content.secondary}
        </button>
        {showEmailForm && (
          <form onSubmit={handleEmailAuth} className="space-y-3">
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Email"
              className="w-full rounded-xl border border-zinc-700 bg-zinc-900/50 px-3 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
            />
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              className="w-full rounded-xl border border-zinc-700 bg-zinc-900/50 px-3 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
            />
            <button
              type="submit"
              disabled={isBusy}
              className="w-full rounded-full bg-zinc-100 px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-zinc-200 disabled:opacity-50"
            >
              {isBusy && authAction === "email"
                ? "Please wait..."
                : isSignIn
                  ? "Continue"
                  : "Create account"}
            </button>
          </form>
        )}
        {message && <p className="text-sm text-zinc-400">{message}</p>}

        <p className="pt-2 text-center text-sm text-zinc-500">
          {content.footerText}{" "}
          <Link className="text-zinc-300 hover:text-white" href={content.footerHref}>
            {content.footerAction}
          </Link>
        </p>
      </div>

      <p className="text-xs text-zinc-600">
        By continuing, you agree to Veritake&apos;s Terms of Service and Privacy Policy.
      </p>
    </section>
  );
}
