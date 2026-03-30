"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { createClient } from "@/lib/supabase/client";

export function AppHeader() {
  const router = useRouter();
  const supabase = useMemo(() => createClient(), []);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    supabase.auth.getUser().then(({ data, error }) => {
      if (!active || error) return;
      setUserEmail(data.user?.email ?? null);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUserEmail(session?.user?.email ?? null);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, [supabase]);

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.refresh();
  }

  return (
    <header className="relative z-10 flex items-center justify-between px-6 py-6 md:px-10">
      <div className="flex items-center gap-2 text-sm font-semibold tracking-[0.2em] text-zinc-300">
        <span className="text-base text-white">V</span>
        <span>VERITAKE</span>
      </div>
      <div className="flex items-center gap-2">
        {userEmail ? (
          <>
            <span className="hidden text-xs text-zinc-400 md:inline">{userEmail}</span>
            <button
              type="button"
              onClick={handleSignOut}
              className="rounded-full border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-200 transition hover:bg-zinc-900 hover:text-white"
            >
              Sign out
            </button>
          </>
        ) : (
          <>
            <Link
              href="/sign-in"
              className="rounded-full border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-200 transition hover:bg-zinc-900 hover:text-white"
            >
              Sign in
            </Link>
            <Link
              href="/sign-up"
              className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-black transition hover:bg-zinc-200"
            >
              Sign up
            </Link>
          </>
        )}
      </div>
    </header>
  );
}
