"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { createClient } from "@/lib/supabase/client";

type AuthVariant = "sign-in" | "sign-up";

type AuthPanelProps = {
  variant: AuthVariant;
};

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
  const supabase = useMemo(() => createClient(), []);
  const content = panelContent[variant];
  const isSignIn = variant === "sign-in";
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleGoogleAuth() {
    setIsBusy(true);
    setMessage(null);
    const redirectTo = `${window.location.origin}/auth/callback?next=/`;
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo },
    });
    if (error) {
      setMessage(error.message);
      setIsBusy(false);
    }
  }

  async function handleEmailAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsBusy(true);
    setMessage(null);

    if (isSignIn) {
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
      return;
    }

    const emailRedirectTo = `${window.location.origin}/auth/callback?next=/`;
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
          className="w-full rounded-full bg-white px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-zinc-200"
        >
          {content.primary}
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
              {isSignIn ? "Continue" : "Create account"}
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
