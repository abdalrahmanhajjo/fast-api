"""Shared / generic response schemas."""

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Message(BaseModel):
    """Generic informational response."""

    detail: str


class PageMeta(BaseModel):
    page: int = Field(..., examples=[1])
    limit: int = Field(..., examples=[10])
    total: int = Field(..., examples=[45])
    total_pages: int = Field(..., examples=[5])


class Page(PageMeta, Generic[T]):
    """Paginated envelope. The item key is overridden per-resource."""

    items: List[T] = []
