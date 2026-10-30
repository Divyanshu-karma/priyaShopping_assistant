"""In-memory order preview, confirmation, and order retrieval service.

All calculations use integer paise internally to avoid floating-point issues,
and return rounded two-decimal float values in INR.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import threading
from typing import Dict, List, Optional
import uuid

from backend.app.catalogue import get_product_by_id
from backend.app.schemas import (
    OrderItemRequest,
    OrderPreviewItem,
    OrderPreviewResponse,
    OrderConfirmResponse,
    OrderResponse,
)


class OrderError(Exception):
    """Base exception for order service."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ProductNotFoundError(OrderError):
    def __init__(self, product_id: str):
        super().__init__(f"Product with ID '{product_id}' was not found in catalogue.", status_code=404)


class PreviewNotFoundError(OrderError):
    def __init__(self, preview_id: str):
        super().__init__(f"Preview with ID '{preview_id}' not found.", status_code=404)


class PreviewAlreadyConfirmedError(OrderError):
    def __init__(self, preview_id: str):
        super().__init__(
            f"Preview with ID '{preview_id}' is already confirmed or no longer pending.",
            status_code=409,
        )


class ConfirmationRequiredError(OrderError):
    def __init__(self):
        super().__init__(
            "Explicit affirmative confirmation is required (confirmed must be true).",
            status_code=400,
        )


class InMemoryOrderService:
    def __init__(self):
        self._lock = threading.Lock()
        # Storage: preview_id -> dict
        self._previews: Dict[str, dict] = {}
        # Storage: order_id -> dict
        self._orders: Dict[str, dict] = {}

    @staticmethod
    def _inr_to_paise(amount: float) -> int:
        """Convert INR float to exact integer paise."""
        dec = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return int(dec * 100)

    @staticmethod
    def _paise_to_inr(paise: int) -> float:
        """Convert integer paise back to INR float."""
        return float(Decimal(paise) / Decimal(100))

    def create_preview(self, items: List[OrderItemRequest]) -> OrderPreviewResponse:
        """
        Validate products, calculate backend-authoritative line totals and grand total,
        and generate an in-memory preview with status 'awaiting_confirmation'.
        """
        if not items:
            raise OrderError("Order preview requires at least one item.", status_code=400)

        preview_items: List[OrderPreviewItem] = []
        total_paise = 0

        with self._lock:
            for item in items:
                product = get_product_by_id(item.product_id)
                if not product:
                    raise ProductNotFoundError(item.product_id)

                if item.quantity <= 0:
                    raise OrderError(f"Quantity for {item.product_id} must be at least 1.", status_code=422)

                unit_paise = self._inr_to_paise(product.price_inr)
                line_paise = unit_paise * item.quantity
                total_paise += line_paise

                preview_items.append(
                    OrderPreviewItem(
                        product_id=product.id,
                        name=product.name,
                        unit_price_inr=self._paise_to_inr(unit_paise),
                        quantity=item.quantity,
                        line_total_inr=self._paise_to_inr(line_paise),
                    )
                )

            preview_id = f"prev_{uuid.uuid4().hex[:12]}"
            total_inr = self._paise_to_inr(total_paise)

            preview_record = {
                "preview_id": preview_id,
                "items": [item.model_dump() for item in preview_items],
                "subtotal_inr": total_inr,
                "total_inr": total_inr,
                "status": "awaiting_confirmation",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self._previews[preview_id] = preview_record

            return OrderPreviewResponse(
                preview_id=preview_id,
                items=preview_items,
                subtotal_inr=total_inr,
                total_inr=total_inr,
                status="awaiting_confirmation",
                currency="INR",
                demo_order=True,
            )

    def confirm_order(self, preview_id: str, confirmed: bool) -> OrderConfirmResponse:
        """
        Confirm an existing pending preview.
        Enforces:
        - confirmed must be true
        - preview must exist
        - preview must not already be confirmed (prevents duplicate orders)
        """
        if not confirmed:
            raise ConfirmationRequiredError()

        with self._lock:
            preview = self._previews.get(preview_id)
            if not preview:
                raise PreviewNotFoundError(preview_id)

            if preview["status"] != "awaiting_confirmation":
                raise PreviewAlreadyConfirmedError(preview_id)

            # Mark preview as confirmed
            preview["status"] = "confirmed"
            confirmed_at = datetime.now(timezone.utc).isoformat()
            order_id = f"ord_{uuid.uuid4().hex[:12]}"

            items = [OrderPreviewItem(**item) for item in preview["items"]]
            order_record = {
                "order_id": order_id,
                "preview_id": preview_id,
                "items": preview["items"],
                "total_inr": preview["total_inr"],
                "status": "confirmed_demo",
                "currency": "INR",
                "demo_order": True,
                "created_at": confirmed_at,
            }
            self._orders[order_id] = order_record

            return OrderConfirmResponse(
                order_id=order_id,
                preview_id=preview_id,
                items=items,
                total_inr=preview["total_inr"],
                currency="INR",
                status="confirmed_demo",
                demo_order=True,
                confirmed_at=confirmed_at,
            )

    def get_order(self, order_id: str) -> Optional[OrderResponse]:
        """Retrieve order by order_id or return None."""
        with self._lock:
            order = self._orders.get(order_id)
            if not order:
                return None

            return OrderResponse(
                order_id=order["order_id"],
                preview_id=order["preview_id"],
                items=[OrderPreviewItem(**item) for item in order["items"]],
                total_inr=order["total_inr"],
                currency="INR",
                status=order["status"],
                demo_order=True,
                created_at=order["created_at"],
            )

    def reset_state(self) -> None:
        """Helper to reset in-memory storage (used in tests)."""
        with self._lock:
            self._previews.clear()
            self._orders.clear()


# Singleton service instance
order_service = InMemoryOrderService()
