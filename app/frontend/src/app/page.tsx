"use client";

import { useMemo, useState } from "react";

type AuthMode = "login" | "signup";

const sessions = [
  "Portfolio rebalance strategy",
  "Daily macro signal review",
  "Evaluate EUR/USD momentum",
  "Risk model discussion",
  "Backtest agent pipeline",
  "Compare two trading workflows",
];

const messages = [
  {
    role: "assistant",
    content:
      "Ready when you are. Ask about a strategy, asset, portfolio setup, or run a structured workflow.",
  },
  { role: "user", content: "Show me today's macro-aware setup for a conservative portfolio." },
  {
    role: "assistant",
    content:
      "I can do that. I will pull the latest signal context, evaluate risk budget, and propose allocations with reasoning.",
  },
];

const reasoningSteps = [
  { label: "Context retrieval", detail: "Loading market snapshot and prior session memory", status: "done" },
  { label: "Signal fusion", detail: "Combining macro + technical + news sentiment", status: "running" },
  { label: "Risk constraints", detail: "Applying exposure, volatility, and drawdown limits", status: "queued" },
  { label: "Allocation draft", detail: "Preparing candidate portfolio and explanations", status: "queued" },
];

function statusClass(status: string) {
  if (status === "done") {
    return "bg-emerald-500";
  }
  if (status === "running") {
    return "bg-amber-400";
  }
  return "bg-zinc-600";
}

export default function HomePage() {
  const [authMode, setAuthMode] = useState<AuthMode | null>(null);
  const [selectedSession, setSelectedSession] = useState(0);

  const modalTitle = useMemo(() => {
    if (authMode === "login") {
      return "Log in";
    }
    if (authMode === "signup") {
      return "Sign up for free";
    }
    return "";
  }, [authMode]);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[270px_1fr_340px]">
        <aside className="border-b border-zinc-800 bg-zinc-950/95 p-4 lg:border-b-0 lg:border-r">
          <h2 className="mb-4 text-sm font-semibold tracking-wide text-zinc-400">Chats</h2>
          <button className="mb-4 w-full rounded-lg border border-zinc-700 px-3 py-2 text-left text-sm hover:bg-zinc-900">
            + New chat
          </button>
          <div className="space-y-1">
            {sessions.map((session, index) => {
              const isActive = index === selectedSession;
              return (
                <button
                  key={session}
                  onClick={() => setSelectedSession(index)}
                  className={`w-full rounded-lg px-3 py-2 text-left text-sm transition ${
                    isActive ? "bg-zinc-800 text-zinc-100" : "text-zinc-300 hover:bg-zinc-900"
                  }`}
                  type="button"
                >
                  {session}
                </button>
              );
            })}
          </div>
        </aside>

        <section className="flex min-h-[60vh] flex-col border-b border-zinc-800 lg:border-b-0 lg:border-r">
          <header className="flex items-center justify-end gap-2 border-b border-zinc-800 px-4 py-3">
            <button
              type="button"
              onClick={() => setAuthMode("login")}
              className="rounded-full border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-100 hover:bg-zinc-900"
            >
              Log in
            </button>
            <button
              type="button"
              onClick={() => setAuthMode("signup")}
              className="rounded-full bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 hover:bg-zinc-200"
            >
              Sign up for free
            </button>
          </header>

          <div className="flex-1 space-y-4 overflow-y-auto px-4 py-6">
            {messages.map((message, index) => {
              const isUser = message.role === "user";
              return (
                <div key={`${message.role}-${index}`} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-2xl rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      isUser ? "bg-zinc-700 text-zinc-100" : "bg-zinc-900 text-zinc-200"
                    }`}
                  >
                    {message.content}
                  </div>
                </div>
              );
            })}
          </div>

          <footer className="border-t border-zinc-800 p-4">
            <div className="rounded-2xl border border-zinc-700 bg-zinc-900 px-4 py-3">
              <input
                className="w-full bg-transparent text-sm text-zinc-100 placeholder-zinc-500 outline-none"
                placeholder="Ask anything about your strategy..."
                type="text"
              />
            </div>
          </footer>
        </section>

        <aside className="bg-zinc-950 p-4">
          <h2 className="mb-1 text-sm font-semibold tracking-wide text-zinc-400">Workflow reasoning</h2>
          <p className="mb-4 text-xs text-zinc-500">Session: {sessions[selectedSession]}</p>
          <div className="space-y-3">
            {reasoningSteps.map((step) => (
              <div key={step.label} className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className={`h-2.5 w-2.5 rounded-full ${statusClass(step.status)}`} />
                  <p className="text-sm font-medium text-zinc-100">{step.label}</p>
                </div>
                <p className="text-xs text-zinc-400">{step.detail}</p>
              </div>
            ))}
          </div>
        </aside>
      </div>

      {authMode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/65 px-4">
          <div className="w-full max-w-md rounded-2xl border border-zinc-700 bg-zinc-900 p-5 shadow-2xl">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h3 className="text-xl font-semibold text-zinc-100">{modalTitle}</h3>
                <p className="mt-1 text-sm text-zinc-400">Auth backend will be connected with FastAPI JWT later.</p>
              </div>
              <button
                type="button"
                onClick={() => setAuthMode(null)}
                className="rounded-md px-2 py-1 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
              >
                x
              </button>
            </div>

            <div className="space-y-3">
              <input
                type="email"
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none placeholder:text-zinc-500 focus:border-zinc-500"
                placeholder="Email"
              />
              <input
                type="password"
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none placeholder:text-zinc-500 focus:border-zinc-500"
                placeholder="Password"
              />
              {authMode === "signup" && (
                <input
                  type="password"
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm outline-none placeholder:text-zinc-500 focus:border-zinc-500"
                  placeholder="Confirm password"
                />
              )}
              <button
                type="button"
                className="mt-1 w-full rounded-lg bg-zinc-100 px-3 py-2 text-sm font-semibold text-zinc-900 hover:bg-zinc-200"
              >
                {authMode === "login" ? "Continue" : "Create account"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
