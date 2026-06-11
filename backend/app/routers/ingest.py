from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import ValidationError as PydanticValidationError

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.email import EmailIngestRequest
from app.services.ingest_service import ingest_email, get_job_status, seed_from_json
from app.utils.exceptions import CRMException

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest", response_model=ApiResponse)
def ingest(payload: EmailIngestRequest, db: Session = Depends(get_db)):
    """
    Ingest a single email. Idempotent — re-sending same message_id returns 409.
    """
    try:
        result = ingest_email(payload, db)
        if result["duplicate"]:
            return ApiResponse.fail(
                error_code="DUPLICATE_MESSAGE_ID",
                message=f"Email '{payload.message_id}' already exists",
                details=result,
            )
        return ApiResponse.ok(data=result, message="Email ingested successfully")
    except PydanticValidationError as e:
        return ApiResponse.fail(
            error_code="VALIDATION_ERROR",
            message="Invalid email payload",
            details=str(e),
        )
    except CRMException as e:
        raise HTTPException(status_code=e.status_code, detail={
            "error_code": e.error_code,
            "message": e.message,
            "details": e.details,
        })
    except Exception as e:
        return ApiResponse.fail(
            error_code="INGEST_ERROR",
            message="Failed to ingest email",
            details=str(e),
        )


@router.get("/status/{job_id}", response_model=ApiResponse)
def get_status(job_id: str, db: Session = Depends(get_db)):
    """Check processing status of an ingested email by job_id."""
    result = get_job_status(job_id, db)
    if not result:
        return ApiResponse.fail(
            error_code="JOB_NOT_FOUND",
            message=f"No job found with id '{job_id}'",
        )
    return ApiResponse.ok(data=result)


@router.post("/seed", response_model=ApiResponse)
def seed_dataset(db: Session = Depends(get_db)):
    """
    Seed the database from email-data-advanced.json.
    Safe to call multiple times — duplicates are skipped.
    """
    try:
        result = seed_from_json("../data/email-data-advanced.json", db)
        return ApiResponse.ok(
            data=result,
            message=f"Seeded {result['ingested']} emails ({result['duplicates']} duplicates skipped)",
        )
    except FileNotFoundError as e:
        return ApiResponse.fail(error_code="FILE_NOT_FOUND", message=str(e))
    except Exception as e:
        return ApiResponse.fail(error_code="SEED_ERROR", message=str(e))