from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.services.rag.retriever import retrieve_chunks
from app.services.classifier_service import classify_email

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/search", response_model=ApiResponse)
def rag_search(q: str = Query(..., description="Search query"), db: Session = Depends(get_db)):
    """Debug endpoint — query the knowledge base and see retrieved chunks + scores."""
    if not q.strip():
        return ApiResponse.fail(error_code="EMPTY_QUERY", message="Query cannot be empty")
    try:
        chunks = retrieve_chunks(q)
        return ApiResponse.ok(
            data={"query": q, "chunks": chunks, "count": len(chunks)},
            message=f"Retrieved {len(chunks)} chunks",
        )
    except Exception as e:
        return ApiResponse.fail(error_code="RAG_ERROR", message=str(e))


@router.post("/classify/{email_id}", response_model=ApiResponse)
def classify(email_id: str, db: Session = Depends(get_db)):
    """Manually trigger classification for a single email."""
    try:
        result = classify_email(email_id, db)
        if result is None:
            return ApiResponse.fail(
                error_code="SKIPPED",
                message="Email was skipped (spam/internal or not found)",
            )
        return ApiResponse.ok(data=result, message="Email classified successfully")
    except Exception as e:
        return ApiResponse.fail(error_code="CLASSIFICATION_ERROR", message=str(e))


@router.get("/analytics/sentiment-trend", response_model=ApiResponse)
def sentiment_trend(
    sender: str = Query(...),
    days: int = Query(30),
    db: Session = Depends(get_db),
):
    from app.services.sentiment_tracker import get_sentiment_trend
    result = get_sentiment_trend(sender, days, db)
    return ApiResponse.ok(data=result)