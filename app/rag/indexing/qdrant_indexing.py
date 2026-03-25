# pyright: reportMissingTypeStubs=false
import json
import sys
from collections.abc import Iterable
from pathlib import Path

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document
from llama_index.core.storage import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

try:
    from app.rag.core.config import (
        CHUNK_OVERLAP,
        CHUNK_SIZE,
        PROCESSED_JSONL_PATH,
        QDRANT_COLLECTION,
    )
    from app.rag.ingestion.custom_transformation import CustomTransformation
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[3]
    sys.path.append(str(repo_root))
    from app.rag.core.config import (
        CHUNK_OVERLAP,
        CHUNK_SIZE,
        PROCESSED_JSONL_PATH,
        QDRANT_COLLECTION,
    )
    from app.rag.ingestion.custom_transformation import CustomTransformation


class QdrantIndexing:
    def __init__(
        self,
        collection_name: str,
        qdrant_url: str = "http://localhost:6333",
        api_key: str = "",
        embedding_model: str = "text-embedding-3-small",
    ) -> None:
        self.collection_name: str = collection_name
        self.client: QdrantClient = QdrantClient(url=qdrant_url, api_key=api_key)
        self.embedding_model: OpenAIEmbedding = OpenAIEmbedding(model=embedding_model)

    @staticmethod
    def save_jsonl_snapshot(docs: Iterable[Document], out_path: str) -> None:
        path = Path(out_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for i, doc in enumerate(docs, start=1):
                row = {
                    "id": (doc.metadata or {}).get("doc_hash", f"doc_{i}"),
                    "text": doc.text,
                    "metadata": doc.metadata,
                }
                _ = f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def build_qdrant_index(self, docs: list[Document]) -> VectorStoreIndex:
        # 1) Chunking
        splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        nodes = splitter.get_nodes_from_documents(docs)

        # 2) Qdrant vector store
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            enable_hybrid=True,
            fastembed_sparse_model="Qdrant/bm25",
            batch_size=20
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # 3) Vector store index
        return VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
            embed_model=self.embedding_model,
        )


def main() -> None:
    transformer = CustomTransformation(collection_name="company_docs")
    repo_root = Path(__file__).resolve().parents[3]
    raw_data_dir = repo_root / "app/rag/data/raw"
    processed_jsonl_path = repo_root / PROCESSED_JSONL_PATH

    docs = SimpleDirectoryReader(input_dir=str(raw_data_dir), recursive=True).load_data()
    transformed_docs, _stats = transformer.transform_documents(docs)

    indexer = QdrantIndexing(collection_name=QDRANT_COLLECTION)
    indexer.save_jsonl_snapshot(transformed_docs, str(processed_jsonl_path))
    _ = indexer.build_qdrant_index(transformed_docs)
    print(f"Indexed {len(transformed_docs)} transformed documents into Qdrant.")


if __name__ == "__main__":
    main()

