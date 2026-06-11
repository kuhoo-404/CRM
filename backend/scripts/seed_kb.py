"""
One-time script to chunk and embed all knowledge base documents into ChromaDB.
Run from backend/ directory:
    python scripts/seed_kb.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag.chunker import chunk_all_documents
from app.services.rag.embedder import embed_texts
from app.services.rag.vector_store import upsert_chunks, get_collection_count
from app.config import get_settings

settings = get_settings()


def main():
    print(f"Loading documents from: {settings.KB_DIR}")
    chunks = chunk_all_documents()
    print(f"Created {len(chunks)} chunks from knowledge base")

    if not chunks:
        print("ERROR: No chunks created. Check KB_DIR path in .env")
        return

    print("Embedding chunks (first run downloads model ~90MB)...")
    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts)
    print(f"Embedded {len(embeddings)} chunks")

    print("Upserting into ChromaDB...")
    count = upsert_chunks(chunks, embeddings)
    total = get_collection_count()
    print(f"Done. Inserted {count} chunks. Total in collection: {total}")


if __name__ == "__main__":
    main()