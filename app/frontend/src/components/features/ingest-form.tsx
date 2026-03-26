import { useState } from "react";

import { ingestAndIndex } from "@/lib/api/ingest";
import type { RagIngestResponse } from "@/lib/types/rag";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export function IngestForm() {
  const [urlsRaw, setUrlsRaw] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RagIngestResponse | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const urls = urlsRaw
      .split("\n")
      .map((url) => url.trim())
      .filter(Boolean);

    try {
      const response = await ingestAndIndex({
        urls,
        pdf_paths: [],
        pdf_recursive: false,
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
        <CardTitle>RAG Ingest + Index (Admin)</CardTitle>
        <CardDescription>Trigger ingestion/indexing job from UI.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <form className="space-y-3" onSubmit={handleSubmit}>
          <Textarea
            placeholder="One URL per line"
            value={urlsRaw}
            onChange={(event) => setUrlsRaw(event.target.value)}
          />
          <div className="flex items-center gap-2">
            <Button type="submit" disabled={loading}>
              {loading ? "Running..." : "Run Ingest + Index"}
            </Button>
            <Badge variant="secondary">TODO: add API key guard</Badge>
          </div>
        </form>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {result && (
          <div className="space-y-2 rounded-lg border border-zinc-200 p-4 text-sm">
            <p><span className="font-semibold">Input:</span> {result.input_count}</p>
            <p><span className="font-semibold">Transformed:</span> {result.transformed_count}</p>
            <p><span className="font-semibold">Indexed:</span> {result.indexed_count}</p>
            <p><span className="font-semibold">Collection:</span> {result.collection_name}</p>
            <p className="break-all">
              <span className="font-semibold">Snapshot:</span> {result.snapshot_path}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
