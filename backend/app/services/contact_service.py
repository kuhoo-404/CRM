from sqlalchemy.orm import Session
from app.models import Contact
from app.models.contact import ContactStatus
from app.utils.exceptions import ContactNotFoundError


def get_contact(email: str, db: Session) -> Contact:
    contact = db.query(Contact).filter(Contact.email == email).first()
    if not contact:
        raise ContactNotFoundError(email)
    return contact


def get_all_contacts(db: Session) -> list:
    return db.query(Contact).order_by(Contact.last_contact_at.desc()).all()


def update_contact_status(email: str, new_status: str, db: Session) -> Contact:
    contact = db.query(Contact).filter(Contact.email == email).first()
    if not contact:
        raise ContactNotFoundError(email)
    try:
        contact.status = ContactStatus(new_status)
    except ValueError:
        from app.utils.exceptions import ValidationError
        raise ValidationError(
            f"Invalid status '{new_status}'",
            details={"allowed": [s.value for s in ContactStatus]}
        )
    db.commit()
    db.refresh(contact)
    return contact