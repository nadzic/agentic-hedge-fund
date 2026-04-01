"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { ANALYZE_TIMEOUT_MS, DICTATION_MAX_DURATION_MS } from "@/components/home/constants";
import { AppHeader } from "@/components/home/app-header";
import { Composer } from "@/components/home/composer";
import { MessagesPane } from "@/components/home/messages-pane";
import { ApiError, API_BASE_URL, apiPost } from "@/lib/api/client";
import {
  AnalyzeResponse,
  ChatMessage,
  ModelInfoResponse,
  TranscriptionResponse,
} from "@/components/home/types";
import {
  formatAssistantReply,
  getAnalyzeErrorMessage,
  getVisibleSuggestions,
  inferHorizon,
  inferSymbol,
  parseRateLimitError,
  parseTranscribeRateLimitError,
} from "@/components/home/utils";

type RateLimitNotice = {
  message: string;
  resetAt: string | null;
  upgradeRequired: boolean;
};

type TranscribeLimitNotice = {
  message: string;
  resetAt: string | null;
};

export default function HomePage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [rateLimitNotice, setRateLimitNotice] = useState<RateLimitNotice | null>(null);
  const [transcribeLimitNotice, setTranscribeLimitNotice] = useState<TranscribeLimitNotice | null>(
    null,
  );
  const [isInputFocused, setIsInputFocused] = useState(false);
  const [isDictating, setIsDictating] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isDictationSupported, setIsDictationSupported] = useState(true);
  const [backendModelName, setBackendModelName] = useState("gpt-4o-mini");
  const inputRef = useRef<HTMLInputElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const stopTimeoutRef = useRef<number | null>(null);
  const transcriptionAbortRef = useRef<AbortController | null>(null);

  const isRateLimited = rateLimitNotice !== null;
  const isDictationRateLimited = transcribeLimitNotice !== null;
  const hasMessages = messages.length > 0;
  const placeholder = useMemo(
    () =>
      hasMessages
        ? "Ask follow-up about the current setup..."
        : "Ask anything about a stock, signal, or strategy...",
    [hasMessages],
  );
  const visibleSuggestions = useMemo(() => getVisibleSuggestions(input), [input]);
  const showSuggestions =
    !hasMessages && isInputFocused && !isLoading && visibleSuggestions.length > 0;

  useEffect(() => {
    if (!window.MediaRecorder || !navigator.mediaDevices?.getUserMedia) {
      setIsDictationSupported(false);
      return undefined;
    }
    setIsDictationSupported(true);
    return () => {
      if (stopTimeoutRef.current !== null) {
        window.clearTimeout(stopTimeoutRef.current);
        stopTimeoutRef.current = null;
      }
      const recorder = mediaRecorderRef.current;
      if (recorder && recorder.state !== "inactive") {
        recorder.stop();
      }
      mediaRecorderRef.current = null;
      for (const track of audioStreamRef.current?.getTracks() ?? []) {
        track.stop();
      }
      audioStreamRef.current = null;
      transcriptionAbortRef.current?.abort();
      transcriptionAbortRef.current = null;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function fetchModelInfo() {
      try {
        const response = await fetch(`${API_BASE_URL}/meta/model`);
        if (!response.ok) {
          return;
        }

        const data = (await response.json()) as ModelInfoResponse;
        if (!active || !data.model?.trim()) {
          return;
        }
        setBackendModelName(data.model.trim());
      } catch {
        // Keep default demo model in UI if request fails.
      }
    }

    void fetchModelInfo();
    return () => {
      active = false;
    };
  }, []);

  async function transcribeRecording(blob: Blob) {
    if (!blob.size) {
      return;
    }

    const controller = new AbortController();
    transcriptionAbortRef.current = controller;
    setIsTranscribing(true);
    try {
      const extension = blob.type.includes("webm") ? "webm" : "wav";
      const file = new File([blob], `dictation.${extension}`, { type: blob.type || "audio/webm" });
      const formData = new FormData();
      formData.append("audio", file);

      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });
      if (!response.ok) {
        if (response.status === 429) {
          let payload: unknown = null;
          try {
            payload = (await response.json()) as unknown;
          } catch {
            payload = null;
          }
          const rateLimitError = parseTranscribeRateLimitError(payload);
          setTranscribeLimitNotice({
            message: rateLimitError.message,
            resetAt: rateLimitError.resetAt,
          });
          return;
        }
        const errorText = await response.text();
        throw new Error(errorText || `Transcription failed with status ${response.status}`);
      }

      const data = (await response.json()) as TranscriptionResponse;
      const transcript = data.text.trim();
      if (!transcript) {
        return;
      }
      setInput((current) => {
        const trimmedCurrent = current.trim();
        return trimmedCurrent.length > 0 ? `${trimmedCurrent} ${transcript}` : transcript;
      });
      inputRef.current?.focus();
    } catch {
      // Keep UX silent for now; user can continue typing manually.
    } finally {
      if (transcriptionAbortRef.current === controller) {
        transcriptionAbortRef.current = null;
      }
      setIsTranscribing(false);
    }
  }

  function stopRecording() {
    if (stopTimeoutRef.current !== null) {
      window.clearTimeout(stopTimeoutRef.current);
      stopTimeoutRef.current = null;
    }

    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
    mediaRecorderRef.current = null;

    for (const track of audioStreamRef.current?.getTracks() ?? []) {
      track.stop();
    }
    audioStreamRef.current = null;
    setIsDictating(false);
  }

  async function startRecording() {
    if (isLoading || isTranscribing || !isDictationSupported || isDictationRateLimited) {
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!window.MediaRecorder) {
        for (const track of stream.getTracks()) {
          track.stop();
        }
        setIsDictationSupported(false);
        return;
      }

      const recorder = new MediaRecorder(stream);
      audioStreamRef.current = stream;
      mediaRecorderRef.current = recorder;
      recordedChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        stopRecording();
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(recordedChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });
        recordedChunksRef.current = [];
        void transcribeRecording(audioBlob);
      };

      recorder.start();
      setIsDictating(true);
      stopTimeoutRef.current = window.setTimeout(() => {
        stopRecording();
      }, DICTATION_MAX_DURATION_MS);
    } catch {
      return;
    }
  }

  function toggleDictation() {
    if (isDictating) {
      stopRecording();
      return;
    }
    void startRecording();
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const query = input.trim();
    if (!query || isLoading || isRateLimited) return;

    if (isDictating) {
      stopRecording();
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
      const data = await apiPost<AnalyzeResponse>(
        "/signals/analyze",
        {
          query,
          symbol,
          horizon,
        },
        { signal: abortController.signal },
      );
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: formatAssistantReply(data),
        },
      ]);
    } catch (error) {
      if (error instanceof ApiError && error.status === 429) {
        const rateLimitError = parseRateLimitError(error.payload);
        setRateLimitNotice({
          message: rateLimitError.message,
          resetAt: rateLimitError.resetAt,
          upgradeRequired: rateLimitError.upgradeRequired,
        });
        setMessages((prev) => [
          ...prev,
          {
            id: `assistant-rate-limit-${Date.now()}`,
            role: "assistant",
            content: `${rateLimitError.message}${
              rateLimitError.resetAt ? `\n\nTry again after: ${rateLimitError.resetAt}` : ""
            }`,
          },
        ]);
        return;
      }
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
      isDictating={isDictating}
      isTranscribing={isTranscribing}
      isDictationSupported={isDictationSupported}
      dictationDisabledReason={
        transcribeLimitNotice
          ? `${transcribeLimitNotice.message}${
              transcribeLimitNotice.resetAt
                ? ` (Try again after: ${transcribeLimitNotice.resetAt})`
                : ""
            }`
          : null
      }
      isLoading={isLoading || isRateLimited}
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

      <main className="relative z-10 mx-auto flex h-[calc(100vh-88px)] w-full max-w-5xl flex-col px-6 pb-4">
        {!hasMessages ? (
          <section className="flex min-h-0 flex-1 flex-col items-center justify-center">
            <div className="mb-10 text-center">
              <p className="mb-3 text-xs uppercase tracking-[0.35em] text-zinc-500">
                Market Intelligence Workspace
              </p>
              <h1 className="text-5xl font-semibold tracking-tight text-white md:text-6xl">
                Veritake
              </h1>
            </div>
            <p className="pb-2 text-center text-xs text-zinc-500">Model: {backendModelName}</p>
            <div
              className={`w-full max-w-3xl transition ${
                isRateLimited ? "pointer-events-none blur-[2px] opacity-60" : ""
              }`}
            >
              {composer}
            </div>
          </section>
        ) : (
          <>
            <section
              className={`hide-scrollbar mx-auto min-h-0 w-full max-w-3xl flex-1 overflow-y-auto pb-4 transition ${
                isRateLimited ? "pointer-events-none blur-[2px] opacity-60" : ""
              }`}
            >
              <MessagesPane messages={messages} isLoading={isLoading} />
            </section>

            <section
              className={`sticky bottom-0 mt-2 bg-linear-to-t from-black via-black/95 to-transparent pt-3 transition ${
                isRateLimited ? "pointer-events-none blur-[2px] opacity-60" : ""
              }`}
            >
              <p className="pb-2 text-center text-xs text-zinc-500">Model: {backendModelName}</p>
              <div className="mx-auto w-full max-w-3xl">{composer}</div>
            </section>
          </>
        )}
        {isRateLimited && rateLimitNotice && (
          <div className="pointer-events-none absolute inset-x-0 bottom-24 z-30 flex justify-center px-6">
            <div className="pointer-events-auto w-full max-w-3xl rounded-2xl border border-zinc-700 bg-zinc-950/95 p-4 text-sm text-zinc-100 shadow-2xl">
              <p className="font-medium text-white">{rateLimitNotice.message}</p>
              {rateLimitNotice.resetAt && (
                <p className="mt-1 text-xs text-zinc-400">Resets at: {rateLimitNotice.resetAt}</p>
              )}
              {rateLimitNotice.upgradeRequired && (
                <div className="mt-3 flex items-center gap-2">
                  <Link
                    href="/sign-in"
                    className="rounded-full border border-zinc-700 px-4 py-2 text-xs font-medium text-zinc-200 transition hover:bg-zinc-900 hover:text-white"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/sign-up"
                    className="rounded-full bg-white px-4 py-2 text-xs font-semibold text-black transition hover:bg-zinc-200"
                  >
                    Sign up
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
