import Link from "next/link";

export function AppHeader() {
  return (
    <header className="relative z-10 flex items-center justify-between px-6 py-6 md:px-10">
      <div className="flex items-center gap-2 text-sm font-semibold tracking-[0.2em] text-zinc-300">
        <span className="text-base text-white">V</span>
        <span>VERITAKE</span>
      </div>
      <div className="flex items-center gap-2">
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
      </div>
    </header>
  );
}
