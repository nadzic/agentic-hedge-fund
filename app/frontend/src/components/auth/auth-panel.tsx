import Link from "next/link";

type AuthVariant = "sign-in" | "sign-up";

type AuthPanelProps = {
  variant: AuthVariant;
};

const panelContent = {
  "sign-in": {
    title: "Log into your account",
    primary: "Login with X",
    secondary: "Login with email",
    socialA: "Login with Google",
    socialB: "Login with Apple",
    footerText: "Don't have an account?",
    footerAction: "Sign up",
    footerHref: "/sign-up",
  },
  "sign-up": {
    title: "Create your account",
    primary: "Sign up with X",
    secondary: "Sign up with email",
    socialA: "Sign up with Apple",
    socialB: "Sign up with Google",
    footerText: "Already have an account?",
    footerAction: "Sign in",
    footerHref: "/sign-in",
  },
} as const;

export function AuthPanel({ variant }: AuthPanelProps) {
  const content = panelContent[variant];

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
          className="w-full rounded-full bg-white px-4 py-2.5 text-sm font-semibold text-black transition hover:bg-zinc-200"
        >
          {content.primary}
        </button>

        <div className="relative py-1">
          <div className="h-px w-full bg-zinc-800" />
        </div>

        <button
          type="button"
          className="w-full rounded-full border border-zinc-700 bg-transparent px-4 py-2.5 text-sm font-medium text-zinc-200 transition hover:border-zinc-500 hover:text-white"
        >
          {content.secondary}
        </button>
        <button
          type="button"
          className="w-full rounded-full border border-zinc-800 bg-transparent px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:border-zinc-600 hover:text-white"
        >
          {content.socialA}
        </button>
        <button
          type="button"
          className="w-full rounded-full border border-zinc-800 bg-transparent px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:border-zinc-600 hover:text-white"
        >
          {content.socialB}
        </button>

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
