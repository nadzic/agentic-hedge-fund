import hashlib
import sys
from datetime import datetime
from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document

try:
    from app.rag.core.constants import CHALLENGE_MARKERS
except ModuleNotFoundError:
    repo_root = Path(__file__).resolve().parents[3]
    sys.path.append(str(repo_root))
    from app.rag.core.constants import CHALLENGE_MARKERS

class CustomTransformation:
    def __init__(self, collection_name: str, min_chars: int = 300) -> None:
        self.collection_name: str = collection_name
        self.min_chars: int = min_chars

    def _normalize_text(self, text: str) -> str:
        # remove whitespace lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def _is_challenge_or_junk(self, text: str) -> bool:
        # check challenge markers
        lowered_text = text.lower()
        return any(marker in lowered_text for marker in CHALLENGE_MARKERS)

    def _build_doc_hash(self, text: str, source_id: str) -> str:
        # hash logic
        payload = f"{source_id}\n{text}".encode("utf-8", errors="ignore")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _infer_source_id(metadata: dict[str, object]) -> str:
        source_id = str(metadata.get("source_id", "")).strip()
        if source_id:
            return source_id

        file_name = str(metadata.get("file_name", "")).strip()
        if file_name:
            return Path(file_name).stem

        file_path = str(metadata.get("file_path", "")).strip()
        if file_path:
            return Path(file_path).stem

        return "unknown_source_id"

    @staticmethod
    def _infer_source_name(metadata: dict[str, object]) -> str:
        source_name = str(metadata.get("source_name", "")).strip()
        if source_name:
            return source_name

        file_path = str(metadata.get("file_path", "")).strip()
        if file_path:
            parts = [part.lower() for part in Path(file_path).parts]
            if "raw" in parts:
                raw_idx = parts.index("raw")
                if raw_idx + 1 < len(parts):
                    return parts[raw_idx + 1]

        source_id = str(metadata.get("source_id", "")).strip()
        if source_id:
            return source_id

        return "unknown_source"

    @staticmethod
    def _detect_company(source_hint: str) -> tuple[str, str] | None:
        hint = source_hint.lower()
        if "nvidia" in hint or "nvda" in hint:
            return ("NVDA", "NVIDIA")
        if "google" in hint or "alphabet" in hint or "googl" in hint:
            return ("GOOGL", "Alphabet")
        return None

    def transform(self, doc: Document) -> Document | None:
        # filter, enrich metadata
        text = self._normalize_text(doc.text or "")
        if not text:
            return None
        if self._is_challenge_or_junk(text):
            return None
        if len(text) < self.min_chars:
            return None
        metadata: dict[str, object] = dict(doc.metadata or {})
        source_id = self._infer_source_id(metadata)
        source_name = self._infer_source_name(metadata)
        metadata["source_id"] = source_id
        metadata["source_name"] = source_name
        metadata["processed_at"] = datetime.now().isoformat()
        metadata["doc_hash"] = self._build_doc_hash(text, source_id)
        metadata["collection_name"] = self.collection_name
        source_hint = " ".join(
            str(metadata.get(key, "")).strip()
            for key in ("source_id", "source_name", "file_name", "file_path")
        )
        company_info = self._detect_company(source_hint)
        if company_info is not None:
            metadata["symbol"], metadata["company"] = company_info
        return Document(text=text, metadata=metadata)

    def transform_documents(self, docs: list[Document]) -> tuple[list[Document], dict[str, int]]:
        # transform all; stats on drops
        out: list[Document] = []
        stats = {
            "input_count": len(docs),
            "output_count": 0,
            "dropped_empty_or_short": 0,
            "dropped_challenge_or_junk": 0,
        }
        for doc in docs:
            raw_text = (doc.text or "").strip()
            if not raw_text or len(raw_text) < self.min_chars:
                stats["dropped_empty_or_short"] += 1
                continue
            if self._is_challenge_or_junk(raw_text):
                stats["dropped_challenge_or_junk"] += 1
                continue
            transformed = self.transform(doc)
            if transformed:
                out.append(transformed)
        stats["output_count"] = len(out)
        return out, stats
  
def main() -> None:
    # cli entry
    transformer = CustomTransformation(collection_name="company_docs")
    repo_root = Path(__file__).resolve().parents[3]
    raw_data_dir = repo_root / "app/rag/data/raw"
    docs = SimpleDirectoryReader(input_dir=str(raw_data_dir), recursive=True).load_data()
    transformed_docs, stats = transformer.transform_documents(docs)

    print(f"Input documents: {stats['input_count']}")
    print(f"Output documents: {stats['output_count']}")
    print(f"Dropped empty or short: {stats['dropped_empty_or_short']}")
    print(f"Dropped challenge or junk: {stats['dropped_challenge_or_junk']}")
    print(f"Total characters: {sum(len(doc.text) for doc in transformed_docs)}")
    for idx, doc in enumerate(transformed_docs, start=1):
        print(f"\nDocument {idx}:")
        print(f"Metadata: {doc.metadata}")
        print(f"Text preview: {doc.text[:500]}{'...' if len(doc.text) > 500 else ''}\n")
    print(f"Total documents: {len(transformed_docs)}")
    print(f"Total characters: {sum(len(doc.text) for doc in transformed_docs)}")
if __name__ == "__main__":
    main()