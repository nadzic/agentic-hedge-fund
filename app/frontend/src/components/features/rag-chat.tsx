import { useState } from "react";

import { queryRag } from "@/lib/api/rag";
import type { RagQueryResponse } from "@/lib/types/rag";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export function RagChat() {
  const [symbol, setSymbol] = useState("NVDA");
  const [query, setQuery] = useState("What were NVIDIA gross margins in Q3 FY25?");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RagQueryResponse | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await queryRag({
        symbol,
        query,
        horizon: "swing",
        top_k: 8,
        sparse_top_k: 20,
        alpha: 0.5,
        max_context_chunks: 5,
      });
      setResult(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>RAG Chat</CardTitle>
          <CardDescription>
            Ask a question and get an answer grounded in retrieved chunks.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-3" onSubmit={handleSubmit}>
            <Input
              placeholder="Ticker symbol (e.g., NVDA)"
              value={symbol}
              onChange={(event) => setSymbol(event.target.value.toUpperCase())}
            />
            <Textarea
              placeholder="Ask a finance question..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <div className="flex items-center gap-2">
              <Button type="submit" disabled={loading}>
                {loading ? "Running..." : "Run RAG Query"}
              </Button>
              <Badge variant="secondary">TODO: stream partial tokens</Badge>
            </div>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-red-600">{error}</p>
          </CardContent>
        </Card>
      )}

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Result</CardTitle>
            <CardDescription>TODO: add pipeline timing and trace link</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <section>
              <h3 className="text-sm font-semibold text-zinc-900">Answer</h3>
              <p className="whitespace-pre-wrap text-sm text-zinc-700">{result.answer}</p>
            </section>
            <section>
              <h3 className="text-sm font-semibold text-zinc-900">Reasoning</h3>
              <p className="whitespace-pre-wrap text-sm text-zinc-700">{result.reasoning ?? "-"}</p>
            </section>
            <section>
              <h3 className="text-sm font-semibold text-zinc-900">Citations</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-zinc-700">
                {result.citations.map((citation) => (
                  <li key={citation} className="break-all">
                    {citation}
                  </li>
                ))}
              </ul>
            </section>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
