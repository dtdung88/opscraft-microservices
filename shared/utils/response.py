from typing import Any, Optional, List
from pydantic import BaseModel

class ApiResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[str]] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

def success_response(data: Any = None, message: str = "Success") -> dict:
    return {
        "success": True,
        "message": message,
        "data": data
    }

def error_response(message: str, errors: List[str] = None) -> dict:
    return {
        "success": False,
        "message": message,
        "errors": errors or []
    }

def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int
) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }