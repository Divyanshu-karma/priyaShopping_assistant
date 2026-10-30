"""Order governance, spending policy enforcement, and lifecycle state transitions."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import json
from typing import Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session

from backend.app.catalogue import get_product_by_id
from backend.app.db.models import (
    ElderProfile,
    FamilyMember,
    OrderRecord,
    OrderItemRecord,
    OrderApproval,
    NotificationOutbox,
    AuditEvent,
)
from backend.app.schemas import (
    OrderItemRequest,
    OrderPreviewItem,
    OrderPreviewResponse,
)


class GovernanceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class OrderNotFoundError(GovernanceError):
    def __init__(self, order_id: str):
        super().__init__(f"Order '{order_id}' not found.", status_code=404)


class InvalidOrderStateError(GovernanceError):
    def __init__(self, current_status: str, requested_action: str):
        super().__init__(
            f"Cannot perform '{requested_action}' when order is in state '{current_status}'.",
            status_code=409,
        )


class UnauthorizedFamilyActionError(GovernanceError):
    def __init__(self, message: str = "Unauthorized family action on this profile."):
        super().__init__(message, status_code=403)


class GovernanceOrderService:
    """Handles persistent orders, policy verification, and family approvals."""

    @staticmethod
    def _inr_to_paise(amount: float) -> int:
        dec = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return int(dec * 100)

    @staticmethod
    def _paise_to_inr(paise: int) -> float:
        return float(Decimal(paise) / Decimal(100))

    def create_persistent_preview(
        self,
        db: Session,
        items_req: List[OrderItemRequest],
        elder_profile_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> OrderPreviewResponse:
        """Create a durable draft/preview order record."""
        if not items_req:
            raise GovernanceError("Order preview requires at least one item.", status_code=400)

        # Idempotency check
        if idempotency_key:
            existing = db.query(OrderRecord).filter(OrderRecord.idempotency_key == idempotency_key).first()
            if existing:
                snapshot = json.loads(existing.quote_snapshot_json)
                return OrderPreviewResponse(
                    preview_id=existing.preview_id,
                    items=[OrderPreviewItem(**it) for it in snapshot["items"]],
                    subtotal_inr=self._paise_to_inr(existing.subtotal_paise),
                    total_inr=self._paise_to_inr(existing.total_paise),
                    status=existing.status,
                    currency="INR",
                    demo_order=False,
                )

        preview_id = f"prev_{uuid.uuid4().hex[:12]}"
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        total_paise = 0
        preview_items: List[OrderPreviewItem] = []
        db_items: List[OrderItemRecord] = []

        for it in items_req:
            prod = get_product_by_id(it.product_id)
            if not prod:
                raise GovernanceError(f"Product '{it.product_id}' was not found.", status_code=404)
            if it.quantity <= 0 or it.quantity > 20:
                raise GovernanceError(f"Invalid quantity {it.quantity} for '{prod.name}'.", status_code=422)

            unit_paise = self._inr_to_paise(prod.price_inr)
            line_paise = unit_paise * it.quantity
            total_paise += line_paise

            preview_item = OrderPreviewItem(
                product_id=prod.id,
                name=prod.name,
                unit_price_inr=self._paise_to_inr(unit_paise),
                quantity=it.quantity,
                line_total_inr=self._paise_to_inr(line_paise),
            )
            preview_items.append(preview_item)
            db_items.append(
                OrderItemRecord(
                    order_id=order_id,
                    product_id=prod.id,
                    product_name=prod.name,
                    unit_price_paise=unit_paise,
                    quantity=it.quantity,
                    line_total_paise=line_paise,
                )
            )

        quote_snapshot = {
            "quoted_at": datetime.now(timezone.utc).isoformat(),
            "items": [it.model_dump() for it in preview_items],
            "total_paise": total_paise,
        }

        order_record = OrderRecord(
            id=order_id,
            elder_profile_id=elder_profile_id,
            preview_id=preview_id,
            idempotency_key=idempotency_key,
            currency="INR",
            subtotal_paise=total_paise,
            total_paise=total_paise,
            status="awaiting_confirmation",
            quote_snapshot_json=json.dumps(quote_snapshot),
            items=db_items,
        )
        db.add(order_record)
        db.commit()
        db.refresh(order_record)

        return OrderPreviewResponse(
            preview_id=preview_id,
            items=preview_items,
            subtotal_inr=self._paise_to_inr(total_paise),
            total_inr=self._paise_to_inr(total_paise),
            status="awaiting_confirmation",
            currency="INR",
            demo_order=False,
        )

    def confirm_by_elder(
        self,
        db: Session,
        preview_id: str,
        confirmed: bool,
        elder_profile_id: Optional[str] = None,
    ) -> Tuple[OrderRecord, str]:
        """
        Handle elder confirmation.
        Evaluates spending limits and family approval policy:
        - If policy requires approval OR order total > limit: status -> 'awaiting_family_approval'
        - Else: status -> 'approved_for_execution'
        """
        if not confirmed:
            raise GovernanceError("Affirmative confirmation required (confirmed must be true).", status_code=400)

        order = db.query(OrderRecord).filter(OrderRecord.preview_id == preview_id).first()
        if not order:
            raise GovernanceError(f"Preview '{preview_id}' not found.", status_code=404)

        if order.status != "awaiting_confirmation":
            raise InvalidOrderStateError(order.status, "confirm_by_elder")

        # Associate profile if provided
        if elder_profile_id:
            order.elder_profile_id = elder_profile_id

        # Policy evaluation
        elder = None
        if order.elder_profile_id:
            elder = db.query(ElderProfile).filter(ElderProfile.id == order.elder_profile_id).first()

        order.elder_confirmed_at = datetime.now(timezone.utc)

        requires_approval = False
        approval_reason = []

        if elder:
            if elder.family_approval_required:
                requires_approval = True
                approval_reason.append("Profile policy mandates family approval for all orders.")
            if order.total_paise > elder.spending_limit_paise:
                requires_approval = True
                limit_inr = self._paise_to_inr(elder.spending_limit_paise)
                approval_reason.append(f"Order total exceeds configured spending limit (₹{limit_inr:.2f}).")
        else:
            # Anonymous / Demo: require approval if total exceeds ₹1,000 threshold
            if order.total_paise > 100000:
                requires_approval = True
                approval_reason.append("High-value order requires family approval.")

        if requires_approval:
            order.status = "awaiting_family_approval"
            # Create approval request
            approval_entry = OrderApproval(
                id=f"appr_{uuid.uuid4().hex[:12]}",
                order_id=order.id,
                status="pending",
                reason_note="; ".join(approval_reason),
            )
            db.add(approval_entry)

            # Queue notification for family
            notif = NotificationOutbox(
                id=f"notif_{uuid.uuid4().hex[:12]}",
                recipient_ref="family_guardians",
                channel="mock",
                event_type="order_awaiting_approval",
                payload_json=json.dumps({
                    "order_id": order.id,
                    "total_inr": self._paise_to_inr(order.total_paise),
                    "reasons": approval_reason,
                }),
                consent_verified=True,
                status="pending",
            )
            db.add(notif)
            message = "Order confirmed by elder. Awaiting family approval before execution."
        else:
            order.status = "approved_for_execution"
            message = "Order confirmed and approved for execution within spending limits."

        # Audit event
        audit = AuditEvent(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            actor_type="elder",
            actor_id=elder.id if elder else "anonymous_elder",
            action="confirm_order",
            target_type="order",
            target_id=order.id,
            details_json=json.dumps({"status": order.status, "total_paise": order.total_paise}),
        )
        db.add(audit)
        db.commit()
        db.refresh(order)

        return order, message

    def process_family_approval(
        self,
        db: Session,
        order_id: str,
        family_member: FamilyMember,
        approved: bool,
        reason_note: Optional[str] = None,
    ) -> OrderRecord:
        """Authorized family member approves or rejects an order awaiting approval."""
        order = db.query(OrderRecord).filter(OrderRecord.id == order_id).first()
        if not order:
            raise OrderNotFoundError(order_id)

        # Authorize: family member must belong to the same elder profile
        if order.elder_profile_id and order.elder_profile_id != family_member.elder_profile_id:
            raise UnauthorizedFamilyActionError("Family member not authorized for this profile's orders.")

        if order.status != "awaiting_family_approval":
            raise InvalidOrderStateError(order.status, "family_approval")

        approval_record = (
            db.query(OrderApproval)
            .filter(OrderApproval.order_id == order.id, OrderApproval.status == "pending")
            .first()
        )

        now = datetime.now(timezone.utc)
        if approved:
            order.status = "approved_for_execution"
            if approval_record:
                approval_record.status = "approved"
                approval_record.actioned_by = family_member.id
                approval_record.actioned_at = now
                approval_record.reason_note = reason_note or "Approved by family guardian."
        else:
            order.status = "cancelled"
            if approval_record:
                approval_record.status = "rejected"
                approval_record.actioned_by = family_member.id
                approval_record.actioned_at = now
                approval_record.reason_note = reason_note or "Rejected by family guardian."

        # Audit event
        audit = AuditEvent(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            actor_type="family",
            actor_id=family_member.id,
            action="approve_order" if approved else "reject_order",
            target_type="order",
            target_id=order.id,
            details_json=json.dumps({"new_status": order.status, "reason": reason_note}),
        )
        db.add(audit)

        # Enqueue notification
        notif = NotificationOutbox(
            id=f"notif_{uuid.uuid4().hex[:12]}",
            recipient_ref=family_member.phone_number or family_member.username,
            channel="mock",
            event_type="order_approved" if approved else "order_rejected",
            payload_json=json.dumps({"order_id": order.id, "status": order.status}),
            consent_verified=family_member.consent_granted,
            status="pending",
        )
        db.add(notif)
        db.commit()
        db.refresh(order)

        return order


governance_service = GovernanceOrderService()
