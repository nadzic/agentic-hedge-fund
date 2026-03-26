import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>RAG Chat</CardTitle>
          <CardDescription>
            Query company documents with retrieval, optional reranking, and generation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link className="text-sm font-medium text-blue-600 hover:underline" href="/rag">
            Open RAG Chat →
          </Link>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Signal Analyzer</CardTitle>
          <CardDescription>
            Run the agent graph and inspect suggested buy/sell/hold signal output.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link className="text-sm font-medium text-blue-600 hover:underline" href="/signals">
            Open Signals →
          </Link>
        </CardContent>
      </Card>
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle>Admin Ingest</CardTitle>
          <CardDescription>
            Trigger ingestion/indexing job for new sources.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link
            className="text-sm font-medium text-blue-600 hover:underline"
            href="/admin/ingest"
          >
            Open Admin Ingest →
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
