import argparse
from collections.abc import Iterator
from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document
from llama_index.readers.file import PDFReader


def _add_pdf_metadata(doc: Document, fallback_source: Path) -> Document:
    metadata = doc.metadata or {}
    file_path = metadata.get("file_path")
    file_name = metadata.get("file_name")
    if file_path:
        source_id = str(Path(file_path).resolve())
    elif file_name:
        source_id = str((fallback_source / file_name).resolve())
    else:
        source_id = str(fallback_source.resolve())
    metadata.setdefault("source_type", "pdf")
    metadata.setdefault("source_id", source_id)
    doc.metadata = metadata
    return doc


def _load_pdf_documents(input_file: Path) -> list[Document]:
    """Load one PDF via PDFReader."""
    reader = SimpleDirectoryReader(
        input_files=[str(input_file)],
        file_extractor={".pdf": PDFReader()},
    )
    return reader.load_data()

def _iter_pdf_files(path: str, recursive: bool) -> list[Path]:
    source = Path(path).resolve()
    if not source.exists():
        raise FileNotFoundError(f"Path does not exist: {source}")

    if source.is_file():
        if source.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a .pdf file, got: {source.name}")
        return [source]

    pdf_files = sorted(source.rglob("*.pdf") if recursive else source.glob("*.pdf"))
    if not pdf_files:
        raise ValueError(f"No PDF files found in directory: {source}")
    return pdf_files


def ingest_pdf_iter(path: str, recursive: bool = False) -> Iterator[Document]:
    """Stream parsed PDF documents one-by-one to reduce peak memory usage."""
    for pdf_file in _iter_pdf_files(path, recursive):
        docs = _load_pdf_documents(pdf_file)
        for doc in docs:
            # Skip raw binary-like content if parsing fails.
            if (doc.text or "").lstrip().startswith("%PDF-"):
                continue
            yield _add_pdf_metadata(doc, pdf_file.parent)


def ingest_pdf(path: str, recursive: bool = False) -> list[Document]:
    """Compatibility wrapper returning all ingested PDF documents."""
    return list(ingest_pdf_iter(path=path, recursive=recursive))

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
    args = parse_args()
    loaded_documents = 0
    total_characters = 0
    if args.text_out_dir:
        out_dir = Path(args.text_out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, doc in enumerate(
            ingest_pdf_iter(path=args.path, recursive=args.recursive), start=1
        ):
            loaded_documents += 1
            total_characters += len(doc.text)
            source = doc.metadata.get("file_name", f"document_{idx}.pdf")
            output_file = out_dir / f"{Path(source).stem}_{idx}.txt"
            output_file.write_text(doc.text, encoding="utf-8")
        print(f"Saved text files to: {out_dir}")
    else:
        for doc in ingest_pdf_iter(path=args.path, recursive=args.recursive):
            loaded_documents += 1
            total_characters += len(doc.text)

    print(f"Loaded documents: {loaded_documents}")
    print(f"Total characters: {total_characters}")

if __name__ == "__main__":
    main()
