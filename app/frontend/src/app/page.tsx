"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import {
  ANALYZE_TIMEOUT_MS,
  API_BASE_URL,
  DICTATION_MAX_DURATION_MS,
  ModelOptionId,
} from "@/components/home/constants";
import { AppHeader } from "@/components/home/app-header";
import { Composer } from "@/components/home/composer";
import { MessagesPane } from "@/components/home/messages-pane";
import { AnalyzeResponse, ChatMessage, TranscriptionResponse } from "@/components/home/types";
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
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isDictationSupported, setIsDictationSupported] = useState(true);
  const [selectedModelId, setSelectedModelId] = useState<ModelOptionId>("chat-gpt-5.4");
  const [isModelMenuOpen, setIsModelMenuOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const stopTimeoutRef = useRef<number | null>(null);
  const transcriptionAbortRef = useRef<AbortController | null>(null);

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
    if (isLoading || isTranscribing || !isDictationSupported) {
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
    if (!query || isLoading) return;

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
      isTranscribing={isTranscribing}
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
