import os
from typing import List, Dict, Any
from pypdf import PdfReader

def extract_pdf_chunks(
    pdf_path: str,
    tenant_id: str,
    department: str,
    clearance_level: int,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Extracts text from a PDF file page-by-page and splits it into manageable chunks,
    attaching complete security metadata and exact PDF page numbers to each chunk.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

    reader = PdfReader(pdf_path)
    filename = os.path.basename(pdf_path)
    chunks = []

    for page_idx, page in enumerate(reader.pages):
        page_number = page_idx + 1
        text = page.extract_text() or ""
        text = text.strip()

        if not text:
            continue

        # Simple character-level sliding window chunker preserving page boundary
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk_text = text[start:end]

            metadata = {
                "tenant_id": tenant_id,
                "department": department,
                "clearance_level": clearance_level,
                "source": filename,
                "page_number": page_number
            }

            chunks.append({
                "text": chunk_text,
                "metadata": metadata
            })

            start += (chunk_size - chunk_overlap)

    return chunks