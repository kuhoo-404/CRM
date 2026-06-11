"""
Retriever
=========
High-level interface — takes a plain text query, returns top-K chunks.
This is what the classifier calls.
"""
from typing import List
from app.services.rag.embedder import embed_query
from app.services.rag.vector_store import similarity_search
from app.config import get_settings

settings = get_settings()


def retrieve_chunks(query: str, top_k: int = None) -> List[dict]:
    """
    Main retrieval function.
    Returns list of dicts: {chunk_text, source_doc, chunk_index, similarity_score}
    """
    if not query or not query.strip():
        return []
    k = top_k or settings.RAG_TOP_K
    query_embedding = embed_query(query)
    return similarity_search(query_embedding, top_k=k)


def format_chunks_for_prompt(chunks: List[dict]) -> str:
    """Format retrieved chunks into a clean string for LLM injection."""
    if not chunks:
        return "No relevant policy context found."
    lines = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(
            f"[{i}] Source: {chunk['source_doc']} "
            f"(relevance: {chunk['similarity_score']})\n{chunk['chunk_text']}"
        )
    return "\n\n".join(lines)