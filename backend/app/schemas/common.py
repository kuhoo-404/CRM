from pydantic import BaseModel
from typing import Any, Optional


class ApiResponse(BaseModel):
    """Standard envelope for every endpoint response."""
    success: bool
    data: Optional[Any] = None
    error_code: Optional[str] = None
    message: Optional[str] = None
    details: Optional[Any] = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "OK") -> "ApiResponse":
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, error_code: str, message: str, details: Any = None) -> "ApiResponse":
        return cls(success=False, error_code=error_code, message=message, details=details)