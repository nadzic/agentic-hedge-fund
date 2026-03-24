import argparse
from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document
from llama_index.readers.file import PDFReader

def _add_pdf_metadata(docs: list[Document], fallback_source: Path) -> list[Document]:
    for doc in docs:
        metadata = doc.metadata or {}
        file_path = metadata.get("file_path")
        file_name = metadata.get("file_name")
        # choose source_id
        if file_path:
            source_id = str(Path(file_path).resolve())
        elif file_name:
            source_id = str((fallback_source / file_name).resolve())
        else:
            source_id = str(fallback_source.resolve())
        metadata.setdefault("source_type", "pdf")
        metadata.setdefault("source_id", source_id)
        doc.metadata = metadata
    return docs


def _load_pdf_documents(input_files: list[str]) -> list[Document]:
    """Force PDF parsing through PDFReader for reliable text extraction."""
    reader = SimpleDirectoryReader(
        input_files=input_files,
        file_extractor={".pdf": PDFReader()},
    )
    docs = reader.load_data()
    # Guard against raw binary-like PDF content slipping through.
    return [doc for doc in docs if not (doc.text or "").lstrip().startswith("%PDF-")]

def ingest_pdf(path: str, recursive: bool = False) -> list[Document]:
    # load pdf(s)
    source = Path(path).resolve()
    if not source.exists():
        raise FileNotFoundError(f"Path does not exist: {source}")
    if source.is_file():
        if source.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a .pdf file, got: {source.name}")
        docs = _load_pdf_documents([str(source)])
        return _add_pdf_metadata(docs, source)
    pdf_files = sorted(source.rglob("*.pdf") if recursive else source.glob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"No PDF files found in directory: {source}")
    docs = _load_pdf_documents([str(file) for file in pdf_files])
    return _add_pdf_metadata(docs, source)

def parse_args() -> argparse.Namespace:
    # parse cli args
    parser = argparse.ArgumentParser(description="Ingest PDF files with LlamaIndex.")
    parser.add_argument("--path", required=True, help="PDF file or directory path.")
    parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Search directories recursively for .pdf files.",
    )
    parser.add_argument(
        "--text-out-dir",
        default="",
        help="Optional directory to save one .txt file per loaded document.",
    )
    return parser.parse_args()

def main() -> None:
    # cli entry
    args = parse_args()
    documents = ingest_pdf(path=args.path, recursive=args.recursive)
    print(f"Loaded documents: {len(documents)}")
    print(f"Total characters: {sum(len(doc.text) for doc in documents)}")
    if args.text_out_dir:
        out_dir = Path(args.text_out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, doc in enumerate(documents, start=1):
            source = doc.metadata.get("file_name", f"document_{idx}.pdf")
            output_file = out_dir / f"{Path(source).stem}_{idx}.txt"
            output_file.write_text(doc.text, encoding="utf-8")
        print(f"Saved text files to: {out_dir}")

if __name__ == "__main__":
    main()
