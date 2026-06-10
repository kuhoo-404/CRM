from fastapi import APIRouter
from app.services.thread_service import get_threads

router = APIRouter()

@router.get("/threads")
def fetch_threads():
    return get_threads()