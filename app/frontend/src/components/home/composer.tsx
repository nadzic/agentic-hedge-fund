import { FormEvent, RefObject } from "react";

import { MODEL_OPTIONS, ModelOptionId } from "@/components/home/constants";

type ComposerProps = {
  input: string;
  placeholder: string;
  inputRef: RefObject<HTMLInputElement | null>;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onInputChange: (value: string) => void;
  onInputFocus: () => void;
  onInputBlur: () => void;
  selectedModelId: ModelOptionId;
  isModelMenuOpen: boolean;
  onToggleModelMenu: () => void;
  onSelectModel: (id: ModelOptionId) => void;
  isDictating: boolean;
  isTranscribing: boolean;
  isDictationSupported: boolean;
  isLoading: boolean;
  onToggleDictation: () => void;
  showSuggestions: boolean;
  visibleSuggestions: string[];
  onSuggestionSelect: (prompt: string) => void;
};

export function Composer({
  input,
  placeholder,
  inputRef,
  onSubmit,
  onInputChange,
  onInputFocus,
  onInputBlur,
  selectedModelId,
  isModelMenuOpen,
  onToggleModelMenu,
  onSelectModel,
  isDictating,
  isTranscribing,
  isDictationSupported,
  isLoading,
  onToggleDictation,
  showSuggestions,
  visibleSuggestions,
  onSuggestionSelect,
}: ComposerProps) {
  const selectedModel = MODEL_OPTIONS.find((option) => option.id === selectedModelId) ?? MODEL_OPTIONS[0];

  return (
    <form onSubmit={onSubmit} className="relative w-full">
      <div className="relative rounded-2xl border border-zinc-800 bg-zinc-950/80 px-5 py-3 shadow-[0_0_60px_rgba(22,78,163,0.12)] backdrop-blur-sm">
        <div className="relative">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(event) => onInputChange(event.target.value)}
                onFocus={onInputFocus}
                onBlur={onInputBlur}
                placeholder={placeholder}
                className="w-full bg-transparent text-sm text-zinc-100 placeholder:text-zinc-500 outline-none"
              />
            </div>
            <div className="relative">
              <button
                type="button"
                onClick={onToggleModelMenu}
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
                        onClick={() => onSelectModel(option.id)}
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
              onClick={onToggleDictation}
              disabled={isLoading || isTranscribing || !isDictationSupported}
              title={isTranscribing ? "Transcribing..." : isDictating ? "Stop dictation" : "Dictation"}
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
              <svg aria-hidden viewBox="0 0 24 24" className="h-4 w-4 fill-none stroke-current" strokeWidth="2">
                <path d="M12 17V7" />
                <path d="m7 12 5-5 5 5" />
              </svg>
            </button>
          </div>
        </div>
        {showSuggestions && (
          <div className="absolute top-full left-0 z-30 mt-2 w-full overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950/98 shadow-xl">
            {visibleSuggestions.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => onSuggestionSelect(prompt)}
                className="flex w-full items-center gap-3 border-b border-zinc-900 px-4 py-2.5 text-left text-sm text-zinc-300 transition last:border-b-0 hover:bg-zinc-900/80 hover:text-zinc-100"
              >
                <svg
                  aria-hidden
                  viewBox="0 0 24 24"
                  className="h-4 w-4 shrink-0 fill-none stroke-zinc-500"
                  strokeWidth="2"
                >
                  <circle cx="11" cy="11" r="7" />
                  <path d="m20 20-3.5-3.5" />
                </svg>
                <span>{prompt}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </form>
  );
}
