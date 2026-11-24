import argparse
import csv
import hashlib
import time
from pathlib import Path
from typing import Any

import chromadb
from pypdf import PdfReader


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "Data"
DATABASE_DIR = ROOT_DIR / "chroma_db"
COLLECTION_NAME = "employee_and_policy_documents"
CHUNK_SIZE = 1200


def safe_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Convert metadata values to types supported by ChromaDB."""
    safe_values: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            safe_values[key] = value
        else:
            safe_values[key] = str(value)
    return safe_values


def make_id(source: str, item_key: str, version: int) -> str:
    """Create a stable ChromaDB ID for a source document or chunk."""
    value = f"{source}:{item_key}:v{version}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def split_text(text: str, max_chars: int = CHUNK_SIZE) -> list[str]:
    """Split text into bounded chunks without dropping any content."""
    remaining = text.strip()
    chunks: list[str] = []

    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break

        split_at = remaining.rfind(" ", 0, max_chars + 1)
        if split_at <= 0:
            split_at = max_chars
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()

    return chunks


def collect_documents() -> list[dict[str, Any]]:
    """Read CSV, Markdown, and PDF files from the Data directory."""
    if not DATA_DIR.is_dir():
        raise FileNotFoundError(f"Data directory does not exist: {DATA_DIR}")

    documents: list[dict[str, Any]] = []

    for csv_path in sorted(DATA_DIR.glob("*.csv")):
        source = csv_path.name
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            for row_number, row in enumerate(csv.DictReader(file), start=1):
                fields = [
                    f"{key}: {value.strip()}"
                    for key, value in row.items()
                    if key and value and value.strip()
                ]
                text = "\n".join(fields)
                if text:
                    documents.append(
                        {
                            "source": source,
                            "item_key": f"row-{row_number}",
                            "text": text,
                            "metadata": {
                                "source": source,
                                "document_type": "employee_record",
                                "access_tier": "internal",
                            },
                        }
                    )

    for text_path in sorted(DATA_DIR.glob("*.md")):
        source = text_path.name
        text = text_path.read_text(encoding="utf-8")
        for chunk_number, chunk in enumerate(split_text(text), start=1):
            documents.append(
                {
                    "source": source,
                    "item_key": f"chunk-{chunk_number}",
                    "text": chunk,
                    "metadata": {
                        "source": source,
                        "document_type": "policy",
                        "access_tier": "internal",
                    },
                }
            )

    for pdf_path in sorted(DATA_DIR.glob("*.pdf")):
        source = pdf_path.name
        reader = PdfReader(str(pdf_path))
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            for chunk_number, chunk in enumerate(split_text(page_text), start=1):
                documents.append(
                    {
                        "source": source,
                        "item_key": f"page-{page_number}-chunk-{chunk_number}",
                        "text": chunk,
                        "metadata": {
                            "source": source,
                            "document_type": "handbook",
                            "access_tier": "internal",
                        },
                    }
                )

    return documents


def get_collection():
    """Open or create the persistent ChromaDB collection."""
    client = chromadb.PersistentClient(path=str(DATABASE_DIR))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return client, collection


def ingest_documents(
    documents: list[dict[str, Any]], collection, batch_size: int = 500
) -> tuple[int, float]:
    """Insert documents into ChromaDB in batches."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero.")
    if not documents:
        print("[INFO] No documents found. Nothing to ingest.")
        return 0, 0.0

    start_time = time.perf_counter()
    ingested = 0

    for batch_start in range(0, len(documents), batch_size):
        batch = documents[batch_start:batch_start + batch_size]
        ids = [
            make_id(str(item["source"]), str(item["item_key"]), 1)
            for item in batch
        ]
        texts = [str(item["text"]) for item in batch]
        metadatas = [safe_metadata(item["metadata"]) for item in batch]

        collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )

        ingested += len(batch)
        print(f"[INGEST] Processed {ingested:,}/{len(documents):,} records")

    elapsed = time.perf_counter() - start_time
    print(f"[DONE] Ingested/upserted {ingested:,} records in {elapsed:.2f} seconds.")
    if elapsed > 0:
        print(f"[BENCHMARK] Throughput: {ingested / elapsed:.2f} records/second")
    print(f"[DB] Collection now contains {collection.count():,} records.")
    return ingested, elapsed


def semantic_search(
    query: str,
    collection,
    results: int = 5,
    access_tier: str | None = None,
) -> None:
    """Search indexed content, optionally filtering by access tier."""
    where_filter = {"access_tier": access_tier} if access_tier else None
    result = collection.query(
        query_texts=[query],
        n_results=min(results, max(collection.count(), 1)),
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    if not ids:
        print("No matching documents found.")
        return

    print(f"\nSearch query: {query}\n")
    for index, (doc_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances), start=1
    ):
        print(f"Result {index} | distance={distance:.4f} | id={doc_id[:12]}...")
        print(f"Source: {metadata.get('source', 'unknown')}")
        print(f"Type: {metadata.get('document_type', 'unknown')}")
        print(f"Metadata: {metadata}")
        print(document[:700] + ("..." if len(document) > 700 else ""))
        print("-" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest employee CSV, Markdown, and PDF files into ChromaDB."
    )
    parser.add_argument(
        "--query",
        type=str,
        help=(
            "Run a semantic search after ingestion, for example: "
            "--query 'software developer in Hyderabad'"
        ),
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Skip ingestion and search the existing ChromaDB collection.",
    )
    parser.add_argument(
        "--access-tier",
        type=str,
        help="Optional metadata filter, for example: --access-tier internal",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Number of search results.")
    args = parser.parse_args()

    _, collection = get_collection()

    if not args.search_only:
        documents = collect_documents()
        ingest_documents(documents, collection)

    if args.query:
        semantic_search(
            query=args.query,
            collection=collection,
            results=max(args.top_k, 1),
            access_tier=args.access_tier,
        )
    elif not args.search_only:
        print("\nExample search:")
        print('python ingestion_pipeline.py --query "software developer in Hyderabad"')


if __name__ == "__main__":
    main()
