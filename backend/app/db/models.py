"""SQLAlchemy models for Priya Shopping Assistant Phase 2."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ElderProfile(Base):
    """Elder user profile for personalized settings, limits, and approvals."""
    __tablename__ = "elder_profiles"

    id = Column(String(50), primary_key=True, index=True)
    display_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, index=True, nullable=True)
    preferred_language = Column(String(20), default="hi")
    delivery_address = Column(Text, nullable=True)
    spending_limit_paise = Column(Integer, default=100000)  # Default ₹1,000 (100,000 paise)
    family_approval_required = Column(Boolean, default=True)
    notification_consent = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    family_members = relationship("FamilyMember", back_populates="elder_profile", cascade="all, delete-orphan")
    orders = relationship("OrderRecord", back_populates="elder_profile")


class FamilyMember(Base):
    """Authorized family members who can view orders, approve purchases, and set policies."""
    __tablename__ = "family_members"

    id = Column(String(50), primary_key=True, index=True)
    elder_profile_id = Column(String(50), ForeignKey("elder_profiles.id"), nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(30), default="guardian")  # admin, guardian, viewer
    phone_number = Column(String(20), nullable=True)
    notification_channel = Column(String(20), default="none")  # none, sms, whatsapp
    consent_granted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    elder_profile = relationship("ElderProfile", back_populates="family_members")


class OrderRecord(Base):
    """Persistent order entity recording exact quotes, elder confirmation, and approval state."""
    __tablename__ = "orders"

    id = Column(String(50), primary_key=True, index=True)
    elder_profile_id = Column(String(50), ForeignKey("elder_profiles.id"), nullable=True, index=True)
    preview_id = Column(String(50), unique=True, nullable=False, index=True)
    idempotency_key = Column(String(100), unique=True, nullable=True, index=True)
    currency = Column(String(10), default="INR")
    subtotal_paise = Column(Integer, nullable=False)
    total_paise = Column(Integer, nullable=False)
    
    # State machine: draft, awaiting_confirmation, awaiting_family_approval, approved_for_execution,
    # confirmed_demo, placing, placed, failed, cancelled, needs_manual_review
    status = Column(String(40), default="draft", nullable=False, index=True)
    
    quote_snapshot_json = Column(Text, nullable=False)  # Immutable snapshot of quoted items and pricing
    elder_confirmed_at = Column(DateTime, nullable=True)
    external_reference = Column(String(100), nullable=True)
    failure_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    elder_profile = relationship("ElderProfile", back_populates="orders")
    items = relationship("OrderItemRecord", back_populates="order", cascade="all, delete-orphan")
    approvals = relationship("OrderApproval", back_populates="order", cascade="all, delete-orphan")


class OrderItemRecord(Base):
    """Line items belonging to an order."""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(String(50), nullable=False)
    product_name = Column(String(200), nullable=False)
    unit_price_paise = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    line_total_paise = Column(Integer, nullable=False)

    # Relationships
    order = relationship("OrderRecord", back_populates="items")


class OrderApproval(Base):
    """Family approval action and audit log for high-value or policy-governed orders."""
    __tablename__ = "order_approvals"

    id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=False, index=True)
    status = Column(String(30), default="pending", nullable=False)  # pending, approved, rejected
    requested_at = Column(DateTime, default=utcnow)
    actioned_by = Column(String(50), nullable=True)
    actioned_at = Column(DateTime, nullable=True)
    reason_note = Column(String(255), nullable=True)

    # Relationships
    order = relationship("OrderRecord", back_populates="approvals")


class NotificationOutbox(Base):
    """Idempotent outbox for family alerts and order event notifications."""
    __tablename__ = "notification_outbox"

    id = Column(String(50), primary_key=True, index=True)
    recipient_ref = Column(String(100), nullable=False)
    channel = Column(String(30), default="mock")  # mock, sms, whatsapp
    event_type = Column(String(50), nullable=False)
    payload_json = Column(Text, nullable=False)
    consent_verified = Column(Boolean, default=False)
    status = Column(String(30), default="pending", nullable=False, index=True)  # pending, sent, failed
    retry_count = Column(Integer, default=0)
    error_category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    sent_at = Column(DateTime, nullable=True)


class AuditEvent(Base):
    """Immutable audit log for security, approvals, policy changes, and voice interactions."""
    __tablename__ = "audit_events"

    id = Column(String(50), primary_key=True, index=True)
    actor_type = Column(String(30), nullable=False)  # elder, family, voice_agent, system
    actor_id = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(50), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class CallSessionMapping(Base):
    """Verified telephony session mapping to prevent untrusted caller ID spoofing."""
    __tablename__ = "call_session_mappings"

    id = Column(String(50), primary_key=True, index=True)
    call_sid = Column(String(100), unique=True, nullable=False, index=True)
    elder_profile_id = Column(String(50), ForeignKey("elder_profiles.id"), nullable=False)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
