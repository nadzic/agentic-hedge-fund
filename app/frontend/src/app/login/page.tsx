"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorText, setErrorText] = useState("");
  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorText("");
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        setErrorText(error.message);
        return;
      }
      router.push("/signals");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Login is currently unavailable.";
      setErrorText(message);
    }
  }
  return (
    <form onSubmit={onSubmit} className="max-w-sm space-y-3">
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
      <input
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        type="password"
      />
      <button type="submit">Login</button>
      {errorText && <p>{errorText}</p>}
    </form>
  );
}
