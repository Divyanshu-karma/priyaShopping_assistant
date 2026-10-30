"""Pydantic schemas for Priya Shopping Assistant Phase 1 API."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    status: str = "ok"
    mode: str = "demo"
    catalogue_source: str = "in_memory"
    orders_persistent: bool = True
    live_commerce_enabled: bool = False
    database_mode: Optional[dict] = None
    voice_tools_enabled: bool = True
    family_dashboard_enabled: bool = True



class Product(BaseModel):
    id: str
    name: str
    name_hi: str
    category: str
    price_inr: float
    description: str
    description_hi: Optional[str] = None
    in_stock: bool = True
    rating: Optional[float] = 4.5
    unit: Optional[str] = "item"


class ProductSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100, description="Search query text")
    category: Optional[str] = Field(None, max_length=50, description="Optional category filter")
    max_price: Optional[float] = Field(None, ge=0, description="Optional maximum price in INR")
    limit: Optional[int] = Field(3, ge=1, le=20, description="Max number of items to return")

    @field_validator("query")
    @classmethod
    def strip_and_validate_query(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Query cannot be empty or only whitespace")
        return trimmed


class ProductSearchResponse(BaseModel):
    query: str
    matches: List[Product]
    count: int
    currency: str = "INR"
    demo_data: bool = True


class OrderItemRequest(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(1, ge=1, le=20, description="Positive integer quantity")


class OrderPreviewRequest(BaseModel):
    items: List[OrderItemRequest] = Field(..., min_length=1, max_length=20)


class OrderPreviewItem(BaseModel):
    product_id: str
    name: str
    unit_price_inr: float
    quantity: int
    line_total_inr: float


class OrderPreviewResponse(BaseModel):
    preview_id: str
    items: List[OrderPreviewItem]
    subtotal_inr: float
    total_inr: float
    currency: str = "INR"
    status: str = "awaiting_confirmation"
    demo_order: bool = True
    disclaimer: str = (
        "Demo order preview only. Fictional data. No real order or payment will be made."
    )


class OrderConfirmRequest(BaseModel):
    preview_id: str = Field(..., min_length=1, max_length=100)
    confirmed: bool = Field(..., description="Must explicitly be true to confirm demo order")


class OrderConfirmResponse(BaseModel):
    order_id: str
    preview_id: str
    items: List[OrderPreviewItem]
    total_inr: float
    currency: str = "INR"
    status: str = "confirmed_demo"
    demo_order: bool = True
    confirmed_at: str
    disclaimer: str = (
        "Demo order confirmed. This is mock state only — no real payment, charge, or dispatch has occurred."
    )


class OrderResponse(BaseModel):
    order_id: str
    preview_id: str
    items: List[OrderPreviewItem]
    total_inr: float
    currency: str = "INR"
    status: str
    demo_order: bool = True
    created_at: str
    disclaimer: str = (
        "In-memory demo order. Does not persist across server restarts."
    )


class ErrorDetail(BaseModel):
    detail: str
