import { AuthPanel } from "@/components/auth/auth-panel";

export default function SignInPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-zinc-100">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[minmax(420px,560px)_1fr]">
        <AuthPanel variant="sign-in" />
        <section className="relative hidden lg:block">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_85%_45%,rgba(244,244,245,0.85),rgba(59,130,246,0.32)_42%,rgba(0,0,0,0.92)_72%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_62%_50%,rgba(255,255,255,0.1),transparent_50%)]" />
        </section>
      </div>
    </div>
  );
}
