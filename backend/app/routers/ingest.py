from fastapi import APIRouter
from app.services.ingest_service import load_emails

router = APIRouter()

@router.get("/emails")
def get_emails():
    return load_emails()