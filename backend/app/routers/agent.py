from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/dry-run/{email_id}", response_model=ApiResponse)
def agent_dry_run(email_id: str, db: Session = Depends(get_db)):
    """Run agent in planning mode — shows reasoning trace without executing."""
    try:
        from app.services.rag.retriever import retrieve_chunks
        from app.agent.loop import AgentLoop

        class RagService:
            def retrieve(self, query, top_k=3):
                chunks = retrieve_chunks(query, top_k=top_k)
                return chunks

        loop = AgentLoop(db=db, rag_service=RagService())
        result = loop.run(email_id=email_id, dry_run=True)
        return ApiResponse.ok(data=result, message="Dry run complete")
    except Exception as e:
        return ApiResponse.fail(error_code="AGENT_ERROR", message=str(e))


@router.post("/run/{email_id}", response_model=ApiResponse)
def agent_run(email_id: str, db: Session = Depends(get_db)):
    """Run agent for real — executes tools and updates DB."""
    try:
        from app.services.rag.retriever import retrieve_chunks
        from app.agent.loop import AgentLoop

        class RagService:
            def retrieve(self, query, top_k=3):
                chunks = retrieve_chunks(query, top_k=top_k)
                return chunks

        loop = AgentLoop(db=db, rag_service=RagService())
        result = loop.run(email_id=email_id, dry_run=False)
        return ApiResponse.ok(data=result, message="Agent run complete")
    except Exception as e:
        return ApiResponse.fail(error_code="AGENT_ERROR", message=str(e))