class CRMException(Exception):
    """Base exception for all CRM errors."""
    def __init__(self, error_code: str, message: str, details=None, status_code: int = 400):
        self.error_code = error_code
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(message)


class DuplicateEmailError(CRMException):
    def __init__(self, message_id: str):
        super().__init__(
            error_code="DUPLICATE_MESSAGE_ID",
            message=f"Email with message_id '{message_id}' already exists",
            details={"message_id": message_id},
            status_code=409,
        )


class EmailNotFoundError(CRMException):
    def __init__(self, identifier: str):
        super().__init__(
            error_code="EMAIL_NOT_FOUND",
            message=f"Email not found: {identifier}",
            status_code=404,
        )


class ContactNotFoundError(CRMException):
    def __init__(self, email: str):
        super().__init__(
            error_code="CONTACT_NOT_FOUND",
            message=f"Contact not found: {email}",
            status_code=404,
        )


class ThreadNotFoundError(CRMException):
    def __init__(self, identifier: str):
        super().__init__(
            error_code="THREAD_NOT_FOUND",
            message=f"Thread not found: {identifier}",
            status_code=404,
        )


class ValidationError(CRMException):
    def __init__(self, message: str, details=None):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
            status_code=422,
        )