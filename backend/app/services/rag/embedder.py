"""
Embedder
========
Wraps sentence-transformers for local embedding.
Model: all-MiniLM-L6-v2 — fast, small, good quality, no API key needed.
"""
from typing import List
from functools import lru_cache


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load once, reuse forever. First call takes ~5 seconds."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    return embed_texts([query])[0]