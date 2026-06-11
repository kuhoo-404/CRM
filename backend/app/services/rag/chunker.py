"""
Chunker
=======
Splits .md files into overlapping token chunks ready for embedding.
Uses simple word-based splitting — no external tokenizer needed.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List
from app.config import get_settings

settings = get_settings()


@dataclass
class Chunk:
    source_doc: str
    chunk_index: int
    text: str


def _split_words(text: str, chunk_size: int, overlap: int) -> List[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def chunk_document(file_path: Path) -> List[Chunk]:
    text = file_path.read_text(encoding="utf-8")
    # Remove markdown headers for cleaner chunks but keep content
    lines = [l for l in text.splitlines() if l.strip()]
    clean_text = " ".join(lines)

    raw_chunks = _split_words(
        clean_text,
        chunk_size=settings.CHUNK_SIZE,
        overlap=settings.CHUNK_OVERLAP,
    )

    return [
        Chunk(
            source_doc=file_path.name,
            chunk_index=i,
            text=chunk,
        )
        for i, chunk in enumerate(raw_chunks)
        if chunk.strip()
    ]


def chunk_all_documents(kb_dir: str = None) -> List[Chunk]:
    kb_path = Path(kb_dir or settings.KB_DIR)
    all_chunks = []
    for md_file in sorted(kb_path.glob("*.md")):
        chunks = chunk_document(md_file)
        all_chunks.extend(chunks)
    return all_chunks