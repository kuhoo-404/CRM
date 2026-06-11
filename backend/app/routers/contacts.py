from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.contact import ContactStatusUpdate
from app.services.contact_service import get_contact, get_all_contacts, update_contact_status
from app.utils.exceptions import CRMException

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=ApiResponse)
def list_contacts(db: Session = Depends(get_db)):
    contacts = get_all_contacts(db)
    return ApiResponse.ok(data=[_serialize(c) for c in contacts])


@router.get("/{email}", response_model=ApiResponse)
def get_contact_profile(email: str, db: Session = Depends(get_db)):
    try:
        contact = get_contact(email, db)
        return ApiResponse.ok(data=_serialize(contact))
    except CRMException as e:
        return ApiResponse.fail(e.error_code, e.message, e.details)


@router.patch("/{email}/status", response_model=ApiResponse)
def update_status(email: str, body: ContactStatusUpdate, db: Session = Depends(get_db)):
    try:
        contact = update_contact_status(email, body.status, db)
        return ApiResponse.ok(data=_serialize(contact), message="Status updated")
    except CRMException as e:
        return ApiResponse.fail(e.error_code, e.message, e.details)


def _serialize(c) -> dict:
    return {
        "id": c.id,
        "email": c.email,
        "name": c.name,
        "company": c.company,
        "status": c.status.value,
        "account_value": c.account_value,
        "churn_risk_score": c.churn_risk_score,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "last_contact_at": c.last_contact_at.isoformat() if c.last_contact_at else None,
    }