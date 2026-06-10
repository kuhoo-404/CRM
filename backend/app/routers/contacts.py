from fastapi import APIRouter
from app.services.contact_service import get_contacts

router = APIRouter()


@router.get("/contacts")
def fetch_contacts():
    return get_contacts()