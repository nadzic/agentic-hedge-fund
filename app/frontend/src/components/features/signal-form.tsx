import { useState } from "react";

import { analyzeSignal } from "@/lib/api/signals";
import type { SignalAnalyzeResponse } from "@/lib/types/signals";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export function SignalForm() {
  const [symbol, setSymbol] = useState("NVDA");
  const [query, setQuery] = useState("Analyze NVIDIA near-term risk/reward.");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SignalAnalyzeResponse | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await analyzeSignal({
        symbol,
        query,
        horizon: "swing",
      });
      setResult(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Signal Analyzer</CardTitle>
        <CardDescription>
          Calls the agent graph endpoint and returns a signal recommendation.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <form className="space-y-3" onSubmit={handleSubmit}>
          <Input
            placeholder="Ticker symbol (e.g., NVDA)"
            value={symbol}
            onChange={(event) => setSymbol(event.target.value.toUpperCase())}
          />
          <Textarea
            placeholder="Analysis request..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <div className="flex items-center gap-2">
            <Button type="submit" disabled={loading}>
              {loading ? "Analyzing..." : "Run Signal Analysis"}
            </Button>
            <Badge variant="secondary">TODO: add horizon selector</Badge>
          </div>
        </form>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {result && (
          <div className="space-y-2 rounded-lg border border-zinc-200 p-4">
            <p className="text-sm">
              <span className="font-semibold">Signal:</span> {result.signal}
            </p>
            <p className="text-sm">
              <span className="font-semibold">Confidence:</span> {result.confidence}
            </p>
            <p className="text-sm whitespace-pre-wrap">
              <span className="font-semibold">Reasoning:</span> {result.reasoning}
            </p>
            {result.warning && (
              <p className="text-sm text-amber-700">
                <span className="font-semibold">Warning:</span> {result.warning}
              </p>
            )}
            {result.error && (
              <p className="text-sm text-red-700">
                <span className="font-semibold">Error:</span> {result.error}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
