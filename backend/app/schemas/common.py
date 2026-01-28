"""
Common API Response Schemas
Defines standard response formats for all API endpoints
"""
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Standard API Success Response"""
    code: int = Field(0, description="Response code, 0 for success")
    message: str = Field("success", description="Response message")
    data: Optional[T] = Field(None, description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 0,
                "message": "success",
                "data": {}
            }
        }


class ErrorResponse(BaseModel):
    """Standard Error Response"""
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 400,
                "message": "Invalid request parameters"
            }
        }


class PaginationParams(BaseModel):
    """Pagination Request Parameters"""
    page: int = Field(1, ge=1, description="Page number (starts from 1)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated Response Format"""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    data: list[T] = Field(..., description="List of items")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 100,
                "page": 1,
                "page_size": 20,
                "data": []
            }
        }


# HTTP Status Code Constants
class HttpStatus:
    """HTTP Status Code Constants"""
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


# Custom Error Codes
class ErrorCode:
    """Custom Error Codes"""
    INVALID_PARAMS = 400
    UNAUTHORIZED = 401
    RESOURCE_NOT_FOUND = 404
    INTERNAL_ERROR = 500
    DATA_SOURCE_ERROR = 501
    ANALYSIS_TIMEOUT = 502
    ANALYSIS_FAILED = 503