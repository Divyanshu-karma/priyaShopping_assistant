"""Authenticated Bolna custom-function tool endpoints."""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.security import verify_tool_token
from backend.app.db.models import OrderRecord
from backend.app.db.session import get_db
from backend.app.catalogue import search_catalogue, get_product_by_id
from backend.app.schemas import (
    OrderItemRequest,
    OrderPreviewResponse,
    Product,
)
from backend.app.services.governance import (
    governance_service,
    GovernanceError,
)

router = APIRouter(prefix="/api/v1/voice/tools", tags=["Bolna Voice Tools"])


def require_voice_tool_auth(authorization: Optional[str] = Header(None)) -> bool:
    """Dependency enforcing bearer token authentication for voice tools."""
    if not verify_tool_token(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing voice tool authorization token.",
        )
    return True


class VoiceSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None
    max_price: Optional[float] = Field(None, ge=0)
    limit: Optional[int] = Field(3, ge=1, le=5)


class VoiceSearchResponse(BaseModel):
    query: str
    matches: List[Product]
    count: int
    currency: str = "INR"
    demo_data: bool = True
    spoken_summary: str


class VoiceProductDetailRequest(BaseModel):
    product_id: str


class VoicePreviewRequest(BaseModel):
    items: List[OrderItemRequest]
    elder_profile_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class VoiceConfirmRequest(BaseModel):
    preview_id: str
    confirmed: bool = Field(..., description="Must explicitly be true")
    elder_profile_id: Optional[str] = None


class VoiceConfirmResponse(BaseModel):
    order_id: str
    preview_id: str
    status: str
    total_inr: float
    currency: str = "INR"
    message: str
    demo_data: bool = True


class VoiceOrderStatusRequest(BaseModel):
    order_id: str
    call_sid: Optional[str] = None


class VoiceOrderStatusResponse(BaseModel):
    order_id: str
    status: str
    total_inr: float
    currency: str = "INR"
    created_at: str
    spoken_status: str


@router.post("/search_products", response_model=VoiceSearchResponse)
def voice_search_products(
    body: VoiceSearchRequest,
    _auth: bool = Depends(require_voice_tool_auth),
) -> VoiceSearchResponse:
    """Search mock catalogue for Priya voice agent."""
    matches = search_catalogue(
        query=body.query,
        category=body.category,
        max_price=body.max_price,
        limit=body.limit or 3,
    )

    if not matches:
        spoken = f"No matching products found for '{body.query}'. Would you like to check something else?"
    else:
        top_names = [f"{p.name} for rupees {int(p.price_inr)}" for p in matches[:2]]
        spoken = f"Found {len(matches)} item{'s' if len(matches) > 1 else ''}. The top choice is {top_names[0]}."

    return VoiceSearchResponse(
        query=body.query,
        matches=matches,
        count=len(matches),
        currency="INR",
        demo_data=True,
        spoken_summary=spoken,
    )


@router.post("/get_product_details", response_model=Product)
def voice_get_product_details(
    body: VoiceProductDetailRequest,
    _auth: bool = Depends(require_voice_tool_auth),
) -> Product:
    """Retrieve detailed information for a single product."""
    product = get_product_by_id(body.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{body.product_id}' not found.",
        )
    return product


@router.post("/create_order_preview", response_model=OrderPreviewResponse)
def voice_create_order_preview(
    body: VoicePreviewRequest,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_voice_tool_auth),
) -> OrderPreviewResponse:
    """Create a persistent order preview calculated authoritatively on the backend."""
    try:
        return governance_service.create_persistent_preview(
            db=db,
            items_req=body.items,
            elder_profile_id=body.elder_profile_id,
            idempotency_key=body.idempotency_key,
        )
    except GovernanceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/request_order_confirmation", response_model=VoiceConfirmResponse)
def voice_request_order_confirmation(
    body: VoiceConfirmRequest,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_voice_tool_auth),
) -> VoiceConfirmResponse:
    """
    Explicit affirmative confirmation from elder caller.
    Evaluates profile spending limits and family approval policy.
    Never silently submits orders to external stores.
    """
    try:
        order, msg = governance_service.confirm_by_elder(
            db=db,
            preview_id=body.preview_id,
            confirmed=body.confirmed,
            elder_profile_id=body.elder_profile_id,
        )
        total_inr = governance_service._paise_to_inr(order.total_paise)
        return VoiceConfirmResponse(
            order_id=order.id,
            preview_id=order.preview_id,
            status=order.status,
            total_inr=total_inr,
            currency="INR",
            message=msg,
            demo_data=True,
        )
    except GovernanceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/get_order_status", response_model=VoiceOrderStatusResponse)
def voice_get_order_status(
    body: VoiceOrderStatusRequest,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_voice_tool_auth),
) -> VoiceOrderStatusResponse:
    """Retrieve current status of a confirmed or pending order."""
    order = db.query(OrderRecord).filter(OrderRecord.id == body.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{body.order_id}' not found.",
        )

    total_inr = governance_service._paise_to_inr(order.total_paise)
    status_spoken_map = {
        "awaiting_family_approval": "Your order is waiting for approval from your family member.",
        "approved_for_execution": "Your order has been approved by your family and is ready.",
        "placed": "Your order has been placed successfully.",
        "cancelled": "This order was cancelled.",
        "needs_manual_review": "This order is being reviewed by our support team.",
    }
    spoken = status_spoken_map.get(order.status, f"Order status is {order.status}.")

    return VoiceOrderStatusResponse(
        order_id=order.id,
        status=order.status,
        total_inr=total_inr,
        currency="INR",
        created_at=order.created_at.isoformat(),
        spoken_status=spoken,
    )
