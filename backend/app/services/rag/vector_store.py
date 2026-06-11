"""
Vector Store
============
ChromaDB wrapper. Handles upsert and similarity search.
Collection: "knowledge_base" — persisted to CHROMA_PERSIST_DIR.
"""
import uuid
from typing import List, Optional
import chromadb
from app.config import get_settings

settings = get_settings()

# Module-level client — created once, never cached with lru_cache
_client = None
_collection = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def upsert_chunks(chunks, embeddings: List[List[float]]) -> int:
    collection = get_collection()
    ids = [str(uuid.uuid4()) for _ in chunks]
    documents = [c.text for c in chunks]
    metadatas = [
        {"source_doc": c.source_doc, "chunk_index": c.chunk_index}
        for c in chunks
    ]
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    return len(ids)


def similarity_search(
    query_embedding: List[float],
    top_k: int = 3,
    source_doc_filter: Optional[str] = None,
) -> List[dict]:
    collection = get_collection()
    where = {"source_doc": source_doc_filter} if source_doc_filter else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for i in range(len(results["ids"][0])):
        hits.append({
            "chunk_text": results["documents"][0][i],
            "source_doc": results["metadatas"][0][i]["source_doc"],
            "chunk_index": results["metadatas"][0][i]["chunk_index"],
            "similarity_score": round(1 - results["distances"][0][i], 4),
        })
    return hits


def get_collection_count() -> int:
    return get_collection().count()