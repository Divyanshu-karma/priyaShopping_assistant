"""Notification service supporting mock and opt-in SMS/WhatsApp delivery."""

from datetime import datetime, timezone
import json
from typing import Dict, Optional
import uuid
from sqlalchemy.orm import Session

from backend.app.db.models import NotificationOutbox


class NotificationResult:
    def __init__(self, success: bool, message_id: str, error: Optional[str] = None):
        self.success = success
        self.message_id = message_id
        self.error = error


class NotificationService:
    """Manages transactional outbox notifications with safe mock default."""

    def __init__(self, mode: str = "mock"):
        self.mode = mode

    def send_notification(
        self,
        db: Session,
        recipient_ref: str,
        event_type: str,
        payload: dict,
        channel: str = "mock",
        consent_granted: bool = True,
    ) -> NotificationResult:
        """Enqueue and process notification via outbox."""
        notif_id = f"notif_{uuid.uuid4().hex[:12]}"
        
        # Verify consent
        if not consent_granted:
            outbox_entry = NotificationOutbox(
                id=notif_id,
                recipient_ref=recipient_ref,
                channel=channel,
                event_type=event_type,
                payload_json=json.dumps(payload),
                consent_verified=False,
                status="failed",
                error_category="consent_missing",
            )
            db.add(outbox_entry)
            db.commit()
            return NotificationResult(False, notif_id, "Notification blocked: consent not granted.")

        # In mock mode (default for development/Phase 2)
        outbox_entry = NotificationOutbox(
            id=notif_id,
            recipient_ref=recipient_ref,
            channel=channel,
            event_type=event_type,
            payload_json=json.dumps(payload),
            consent_verified=True,
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
        db.add(outbox_entry)
        db.commit()

        return NotificationResult(True, notif_id)


notification_service = NotificationService(mode="mock")
