"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { ANALYZE_TIMEOUT_MS, API_BASE_URL, ModelOptionId } from "@/components/home/constants";
import { AppHeader } from "@/components/home/app-header";
import { Composer } from "@/components/home/composer";
import { MessagesPane } from "@/components/home/messages-pane";
import {
  AnalyzeResponse,
  ChatMessage,
  DictationConstructor,
  DictationRecognition,
} from "@/components/home/types";
import {
  formatAssistantReply,
  getAnalyzeErrorMessage,
  getVisibleSuggestions,
  inferHorizon,
  inferSymbol,
} from "@/components/home/utils";

export default function HomePage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const [isDictating, setIsDictating] = useState(false);
  const [isDictationSupported, setIsDictationSupported] = useState(true);
  const [selectedModelId, setSelectedModelId] = useState<ModelOptionId>("chat-gpt-5.4");
  const [isModelMenuOpen, setIsModelMenuOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const recognitionRef = useRef<DictationRecognition | null>(null);

  const hasMessages = messages.length > 0;
  const placeholder = useMemo(
    () =>
      hasMessages
        ? "Ask follow-up about the current setup..."
        : "Ask anything about a stock, signal, or strategy...",
    [hasMessages],
  );
  const visibleSuggestions = useMemo(() => getVisibleSuggestions(input), [input]);
  const showSuggestions = !hasMessages && isInputFocused && !isLoading && visibleSuggestions.length > 0;

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

    const abortController = new AbortController();
    const timeoutId = window.setTimeout(() => {
      abortController.abort();
    }, ANALYZE_TIMEOUT_MS);

    try {
      const symbol = inferSymbol(query);
      const horizon = inferHorizon(query);
      const response = await fetch(`${API_BASE_URL}/signals/analyze`, {
        method: "POST",
        signal: abortController.signal,
        headers: {
          "Content-Type": "application/json",
          "X-Model-Preference": selectedModelId,
        },
        body: JSON.stringify({
          query,
          symbol,
          horizon,
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
      const text = getAnalyzeErrorMessage(error, ANALYZE_TIMEOUT_MS);
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: `I could not complete the analysis.\n\n${text}`,
        },
      ]);
    } finally {
      window.clearTimeout(timeoutId);
      setIsLoading(false);
    }
  }

  const composer = (
    <Composer
      input={input}
      placeholder={placeholder}
      inputRef={inputRef}
      onSubmit={onSubmit}
      onInputChange={setInput}
      onInputFocus={() => setIsInputFocused(true)}
      onInputBlur={() => setIsInputFocused(false)}
      selectedModelId={selectedModelId}
      isModelMenuOpen={isModelMenuOpen}
      onToggleModelMenu={() => setIsModelMenuOpen((prev) => !prev)}
      onSelectModel={(id) => {
        setSelectedModelId(id);
        setIsModelMenuOpen(false);
      }}
      isDictating={isDictating}
      isDictationSupported={isDictationSupported}
      isLoading={isLoading}
      onToggleDictation={toggleDictation}
      showSuggestions={showSuggestions}
      visibleSuggestions={visibleSuggestions}
      onSuggestionSelect={(prompt) => {
        setInput(prompt);
        setIsInputFocused(false);
        inputRef.current?.focus();
      }}
    />
  );

  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-zinc-100">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.06),transparent_40%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_10%,rgba(70,109,182,0.22),transparent_45%)]" />
      </div>

      <AppHeader />

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-88px)] w-full max-w-5xl flex-col px-6 pb-8">
        {!hasMessages ? (
          <div className="flex min-h-[calc(100vh-160px)] flex-col items-center justify-center">
            <div className="mb-10 text-center">
              <p className="mb-3 text-xs uppercase tracking-[0.35em] text-zinc-500">
                Market Intelligence Workspace
              </p>
              <h1 className="text-5xl font-semibold tracking-tight text-white md:text-6xl">
                Veritake
              </h1>
            </div>
            <div className="w-full max-w-2xl">{composer}</div>
          </div>
        ) : (
          <>
            <MessagesPane messages={messages} isLoading={isLoading} />
            <div className="pt-4">{composer}</div>
          </>
        )}
      </main>
    </div>
  );
}
