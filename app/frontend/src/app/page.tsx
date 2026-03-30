"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type AnalyzeResponse = {
  symbol: string;
  signal: string;
  confidence: number;
  reasoning: string;
  warning: string | null;
  error: string | null;
};

type DictationResult = {
  transcript: string;
};

type DictationResultList = {
  length: number;
  item(index: number): DictationResult | null;
  [index: number]: DictationResult;
};

type DictationEvent = {
  resultIndex: number;
  results: DictationResultList;
};

type DictationRecognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: DictationEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type DictationConstructor = new () => DictationRecognition;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const MODEL_OPTIONS = [
  {
    id: "opus-4.6",
    label: "Opus 4.6",
    detail: "Deeper reasoning",
  },
  {
    id: "chat-gpt-5.4",
    label: "ChatGPT 5.4",
    detail: "Faster responses",
  },
] as const;

function inferSymbol(query: string): string {
  const candidates = query.match(/\b[A-Z]{1,5}\b/g);
  return candidates?.at(-1) ?? "AAPL";
}

function formatAssistantReply(payload: AnalyzeResponse): string {
  const lines = [
    `Symbol: ${payload.symbol}`,
    `Signal: ${payload.signal.toUpperCase()}`,
    `Confidence: ${(payload.confidence * 100).toFixed(1)}%`,
    "",
    payload.reasoning,
  ];
  if (payload.warning) {
    lines.push("", `Warning: ${payload.warning}`);
  }
  if (payload.error) {
    lines.push("", `Error: ${payload.error}`);
  }
  return lines.join("\n");
}

export default function HomePage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDictating, setIsDictating] = useState(false);
  const [isDictationSupported, setIsDictationSupported] = useState(true);
  const [selectedModelId, setSelectedModelId] = useState<(typeof MODEL_OPTIONS)[number]["id"]>(
    "chat-gpt-5.4"
  );
  const [isModelMenuOpen, setIsModelMenuOpen] = useState(false);
  const recognitionRef = useRef<DictationRecognition | null>(null);

  const hasMessages = messages.length > 0;
  const selectedModel = useMemo(
    () => MODEL_OPTIONS.find((option) => option.id === selectedModelId) ?? MODEL_OPTIONS[0],
    [selectedModelId]
  );

  const placeholder = useMemo(
    () =>
      hasMessages
        ? "Ask follow-up about the current setup..."
        : "Ask anything about a stock, signal, or strategy...",
    [hasMessages]
  );

  useEffect(() => {
    const speechWindow = window as Window & {
      SpeechRecognition?: DictationConstructor;
      webkitSpeechRecognition?: DictationConstructor;
    };
    const Recognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;

    if (!Recognition) {
      setIsDictationSupported(false);
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "sl-SI";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      const transcriptParts: string[] = [];
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const part = event.results[index]?.transcript?.trim();
        if (part) {
          transcriptParts.push(part);
        }
      }
      if (transcriptParts.length === 0) {
        return;
      }
      const transcript = transcriptParts.join(" ").trim();
      setInput((current) => {
        const trimmedCurrent = current.trim();
        return trimmedCurrent.length > 0 ? `${trimmedCurrent} ${transcript}` : transcript;
      });
    };

    recognition.onerror = () => {
      setIsDictating(false);
    };

    recognition.onend = () => {
      setIsDictating(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
      recognitionRef.current = null;
    };
  }, []);

  function toggleDictation() {
    if (isLoading || !isDictationSupported) {
      return;
    }

    if (isDictating) {
      recognitionRef.current?.stop();
      setIsDictating(false);
      return;
    }

    try {
      recognitionRef.current?.start();
      setIsDictating(true);
    } catch {
      setIsDictating(false);
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = input.trim();
    if (!query || isLoading) return;

    if (isDictating) {
      recognitionRef.current?.stop();
      setIsDictating(false);
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const symbol = inferSymbol(query);
      const response = await fetch(`${API_BASE_URL}/signals/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Model-Preference": selectedModelId,
        },
        body: JSON.stringify({
          query,
          symbol,
          horizon: "swing",
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API ${response.status}: ${errorText}`);
      }

      const data = (await response.json()) as AnalyzeResponse;
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: formatAssistantReply(data),
        },
      ]);
    } catch (error) {
      const text = error instanceof Error ? error.message : "Unknown error";
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: `I could not complete the analysis.\n\n${text}`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  const composer = (
    <form onSubmit={onSubmit} className="relative w-full">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-950/80 px-5 py-3 shadow-[0_0_60px_rgba(22,78,163,0.12)] backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={placeholder}
            className="w-full bg-transparent text-sm text-zinc-100 placeholder:text-zinc-500 outline-none"
          />
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsModelMenuOpen((prev) => !prev)}
              className="inline-flex min-w-[104px] shrink-0 items-center justify-between gap-1 whitespace-nowrap rounded-full border border-zinc-700 px-3 py-1.5 text-xs font-medium text-zinc-200 transition hover:bg-zinc-900"
            >
              {selectedModel.label}
              <span className="text-zinc-500">▾</span>
            </button>
            {isModelMenuOpen && (
              <div className="absolute right-0 bottom-12 z-20 w-52 rounded-2xl border border-zinc-700 bg-zinc-900/95 p-2 shadow-xl backdrop-blur">
                {MODEL_OPTIONS.map((option) => {
                  const isSelected = option.id === selectedModelId;
                  return (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => {
                        setSelectedModelId(option.id);
                        setIsModelMenuOpen(false);
                      }}
                      className={`mb-1 w-full rounded-xl px-3 py-2 text-left transition last:mb-0 ${
                        isSelected ? "bg-zinc-800 text-white" : "text-zinc-300 hover:bg-zinc-800/70"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{option.label}</span>
                        {isSelected && <span className="text-xs text-zinc-400">✓</span>}
                      </div>
                      <p className="mt-0.5 text-xs text-zinc-500">{option.detail}</p>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={toggleDictation}
            disabled={isLoading || !isDictationSupported}
            title={isDictating ? "Stop dictation" : "Dictation"}
            className={`inline-flex h-9 w-9 items-center justify-center rounded-full border transition disabled:cursor-not-allowed disabled:opacity-50 ${
              isDictating
                ? "border-red-500/60 bg-red-500/20 text-red-100"
                : "border-zinc-700 bg-zinc-900 text-zinc-100 hover:bg-zinc-800"
            }`}
          >
            {isDictating ? (
              <span className="h-2.5 w-2.5 rounded-[2px] bg-current" />
            ) : (
              <svg
                aria-hidden
                viewBox="0 0 24 24"
                className="h-4 w-4 fill-none stroke-current"
                strokeWidth="1.8"
              >
                <path d="M12 4a3 3 0 0 1 3 3v5a3 3 0 1 1-6 0V7a3 3 0 0 1 3-3Z" />
                <path d="M5 11.5a7 7 0 0 0 14 0" />
                <path d="M12 18.5v2.5" />
              </svg>
            )}
          </button>
          <button
            type="submit"
            disabled={isLoading || input.trim().length === 0}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-zinc-100 text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
            title="Send"
          >
            <svg
              aria-hidden
              viewBox="0 0 24 24"
              className="h-4 w-4 fill-none stroke-current"
              strokeWidth="2"
            >
              <path d="M12 17V7" />
              <path d="m7 12 5-5 5 5" />
            </svg>
          </button>
        </div>
      </div>
    </form>
  );

  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-zinc-100">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.06),transparent_40%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_10%,rgba(70,109,182,0.22),transparent_45%)]" />
      </div>

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

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-88px)] w-full max-w-5xl flex-col px-6 pb-8">
        {!hasMessages ? (
          <div className="flex min-h-[calc(100vh-160px)] flex-col items-center justify-center">
            <div className="mb-10 text-center">
              <p className="mb-3 text-xs uppercase tracking-[0.35em] text-zinc-500">
                Market Intelligence Workspace
              </p>
              <h1 className="text-5xl font-semibold tracking-tight text-white md:text-6xl">Veritake</h1>
            </div>
            <div className="w-full max-w-2xl">{composer}</div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-1">
              {messages.map((message) => {
                const isUser = message.role === "user";
                return (
                  <div
                    key={message.id}
                    className={`mb-5 flex ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    <article
                      className={`max-w-3xl whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                        isUser ? "bg-zinc-800 text-zinc-100" : "bg-zinc-950/90 text-zinc-300"
                      }`}
                    >
                      {message.content}
                    </article>
                  </div>
                );
              })}
              {isLoading && <p className="text-sm text-zinc-500">Analyzing with agents...</p>}
            </div>
            <div className="pt-4">{composer}</div>
          </>
        )}
      </main>
    </div>
  );
}
