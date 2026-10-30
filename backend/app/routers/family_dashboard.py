"""Family Dashboard API for elder profile oversight, spending limits, and order approvals."""

from datetime import datetime, timezone
import json
from typing import Dict, List, Optional
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.security import (
    generate_session_token,
    verify_password,
)
from backend.app.db.models import (
    AuditEvent,
    ElderProfile,
    FamilyMember,
    OrderApproval,
    OrderRecord,
)
from backend.app.db.session import get_db
from backend.app.services.governance import (
    governance_service,
    GovernanceError,
    UnauthorizedFamilyActionError,
)

router = APIRouter(prefix="/api/v1/family", tags=["Family Dashboard"])

# Active sessions store: token -> family_member_id
ACTIVE_SESSIONS: Dict[str, str] = {}


def get_current_family_member(
    db: Session = Depends(get_db),
    priya_family_session: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
) -> FamilyMember:
    """Dependency verifying authenticated family session token."""
    token = priya_family_session
    if not token and authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token or token not in ACTIVE_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to the family dashboard.",
        )

    member_id = ACTIVE_SESSIONS[token]
    member = db.query(FamilyMember).filter(FamilyMember.id == member_id, FamilyMember.is_active == True).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalid or user inactive.",
        )
    return member


# --- Pydantic Schemas ---

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    full_name: str
    role: str
    elder_profile_id: str


class ElderProfileOut(BaseModel):
    id: str
    display_name: str
    phone_number: Optional[str]
    preferred_language: str
    delivery_address: Optional[str]
    spending_limit_inr: float
    family_approval_required: bool
    notification_consent: bool


class PolicyUpdateRequest(BaseModel):
    spending_limit_inr: Optional[float] = Field(None, ge=0)
    family_approval_required: Optional[bool] = None


class OrderSummaryOut(BaseModel):
    id: str
    preview_id: str
    status: str
    total_inr: float
    currency: str
    created_at: str
    items_count: int
    quote_snapshot: dict


class ApprovalActionRequest(BaseModel):
    reason_note: Optional[str] = Field(None, max_length=200)


class AuditEventOut(BaseModel):
    id: str
    actor_type: str
    action: str
    target_type: str
    target_id: Optional[str]
    created_at: str
    details: Optional[dict]


# --- Endpoints ---

@router.post("/auth/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate family member and issue session token and cookie."""
    member = db.query(FamilyMember).filter(FamilyMember.username == body.username).first()
    if not member or not verify_password(body.password, member.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = generate_session_token()
    ACTIVE_SESSIONS[token] = member.id

    # Set secure HttpOnly cookie
    response.set_cookie(
        key="priya_family_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # Can be true in production with HTTPS
    )

    return LoginResponse(
        token=token,
        username=member.username,
        full_name=member.full_name,
        role=member.role,
        elder_profile_id=member.elder_profile_id,
    )


@router.post("/auth/logout")
def logout(
    response: Response,
    priya_family_session: Optional[str] = Cookie(None),
):
    """Sign out and invalidate session."""
    if priya_family_session in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[priya_family_session]
    response.delete_cookie("priya_family_session")
    return {"status": "logged_out"}


@router.get("/auth/me", response_model=LoginResponse)
def get_me(member: FamilyMember = Depends(get_current_family_member)):
    """Get current logged-in family member info."""
    return LoginResponse(
        token="active_session",
        username=member.username,
        full_name=member.full_name,
        role=member.role,
        elder_profile_id=member.elder_profile_id,
    )


@router.get("/profiles", response_model=List[ElderProfileOut])
def get_profiles(
    member: FamilyMember = Depends(get_current_family_member),
    db: Session = Depends(get_db),
):
    """Retrieve elder profiles authorized for this family member."""
    elder = db.query(ElderProfile).filter(ElderProfile.id == member.elder_profile_id).first()
    if not elder:
        return []
    
    return [
        ElderProfileOut(
            id=elder.id,
            display_name=elder.display_name,
            phone_number=elder.phone_number,
            preferred_language=elder.preferred_language,
            delivery_address=elder.delivery_address,
            spending_limit_inr=governance_service._paise_to_inr(elder.spending_limit_paise),
            family_approval_required=elder.family_approval_required,
            notification_consent=elder.notification_consent,
        )
    ]


@router.get("/profiles/{profile_id}", response_model=ElderProfileOut)
def get_profile(
    profile_id: str,
    member: FamilyMember = Depends(get_current_family_member),
    db: Session = Depends(get_db),
):
    """Retrieve single elder profile with strict BOLA authorization check."""
    if profile_id != member.elder_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You are not authorized to view this elder profile.",
        )

    elder = db.query(ElderProfile).filter(ElderProfile.id == profile_id).first()
    if not elder:
        raise HTTPException(status_code=404, detail="Elder profile not found.")

    return ElderProfileOut(
        id=elder.id,
        display_name=elder.display_name,
        phone_number=elder.phone_number,
        preferred_language=elder.preferred_language,
        delivery_address=elder.delivery_address,
        spending_limit_inr=governance_service._paise_to_inr(elder.spending_limit_paise),
        family_approval_required=elder.family_approval_required,
        notification_consent=elder.notification_consent,
    )


@router.patch("/profiles/{profile_id}/policy", response_model=ElderProfileOut)
def update_profile_policy(
    profile_id: str,
    body: PolicyUpdateRequest,
    member: FamilyMember = Depends(get_current_family_member),
    db: Session = Depends(get_db),
):
    """Update spending limit and approval policy with audit logging."""
    if profile_id != member.elder_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot modify policies for other profiles.",
        )

    elder = db.query(ElderProfile).filter(ElderProfile.id == profile_id).first()
    if not elder:
        raise HTTPException(status_code=404, detail="Elder profile not found.")

    changes = {}
    if body.spending_limit_inr is not None:
        old_limit = elder.spending_limit_paise
        new_paise = governance_service._inr_to_paise(body.spending_limit_inr)
        elder.spending_limit_paise = new_paise
        changes["spending_limit_inr"] = {"from": governance_service._paise_to_inr(old_limit), "to": body.spending_limit_inr}

    if body.family_approval_required is not None:
        old_req = elder.family_approval_required
        elder.family_approval_required = body.family_approval_required
        changes["family_approval_required"] = {"from": old_req, "to": body.family_approval_required}

    # Record Audit Event
    audit = AuditEvent(
        id=f"aud_{generate_session_token()[:12]}",
        actor_type="family",
        actor_id=member.id,
        action="update_elder_policy",
        target_type="elder_profile",
        target_id=elder.id,
        details_json=json.dumps(changes),
    )
    db.add(audit)
    db.commit()
    db.refresh(elder)

    return ElderProfileOut(
        id=elder.id,
        display_name=elder.display_name,
        phone_number=elder.phone_number,
        preferred_language=elder.preferred_language,
        delivery_address=elder.delivery_address,
        spending_limit_inr=governance_service._paise_to_inr(elder.spending_limit_paise),
        family_approval_required=elder.family_approval_required,
        notification_consent=elder.notification_consent,
    )


@router.get("/orders", response_model=List[OrderSummaryOut])
def list_family_orders(
    member: FamilyMember = Depends(get_current_family_member),
    db: Session = Depends(get_db),
):
    """List orders belonging to the authorized elder."""
    orders = (
        db.query(OrderRecord)
        .filter(OrderRecord.elder_profile_id == member.elder_profile_id)
        .order_by(OrderRecord.created_at.desc())
        .all()
    )

    out = []
    for ord_rec in orders:
        snapshot = json.loads(ord_rec.quote_snapshot_json) if ord_rec.quote_snapshot_json else {}
        out.append(
            OrderSummaryOut(
                id=ord_rec.id,
                preview_id=ord_rec.preview_id,
                status=ord_rec.status,
                total_inr=governance_service._paise_to_inr(ord_rec.total_paise),
                currency=ord_rec.currency,
                created_at=ord_rec.created_at.isoformat(),
                items_count=len(snapshot.get("items", [])),
                quote_snapshot=snapshot,
            )
        )
    return out


@router.get("/orders/{order_id}", response_model=OrderSummaryOut)
def get_order_detail(
    order_id: str,
    member: FamilyMember = Depends(get_current_family_member),
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific order with ownership verification."""
    order = db.query(OrderRecord).filter(OrderRecord.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    if order.elder_profile_id and order.elder_profile_id != member.elder_profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view orders for other profiles.",
        )

    snapshot = json.loads(order.quote_snapshot_json) if order.quote_snapshot_json else {}
    return OrderSummaryOut(
        id=order.id,
        preview_id=order.preview_id,
        status=order.status,
        total_inr=governance_service._paise_to_inr(order.total_paise),
        currency=order.currency,
        created_at=order.created_at.isoformat(),
        items_count=len(snapshot.get("items", [])),
        quote_snapshot=snapshot,
    )


@router.post("/orders/{order_id}/approve", response_model=OrderSummaryOut)
def approve_order(
    order_id: str,
    body: ApprovalActionRequest,
    member: FamilyMember = Depends(get_current_family_member),
    db: Session = Depends(get_db),
):
    """Approve a pending order requiring family authorization."""
    try:
        updated_order = governance_service.process_family_approval(
            db=db,
            order_id=order_id,
            family_member=member,
            approved=True,
            reason_note=body.reason_note,
        )
        snapshot = json.loads(updated_order.quote_snapshot_json)
        return OrderSummaryOut(
            id=updated_order.id,
            preview_id=updated_order.preview_id,
            status=updated_order.status,
            total_inr=governance_service._paise_to_inr(updated_order.total_paise),
            currency=updated_order.currency,
            created_at=updated_order.created_at.isoformat(),
            items_count=len(snapshot.get("items", [])),
            quote_snapshot=snapshot,
        )
    except GovernanceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/orders/{order_id}/reject", response_model=OrderSummaryOut)
def reject_order(
    order_id: str,
    body: ApprovalActionRequest,
    member: FamilyMember = Depends(get_current_family_member),
    db: Session = Depends(get_db),
):
    """Reject a pending order requiring family authorization."""
    try:
        updated_order = governance_service.process_family_approval(
            db=db,
            order_id=order_id,
            family_member=member,
            approved=False,
            reason_note=body.reason_note,
        )
        snapshot = json.loads(updated_order.quote_snapshot_json)
        return OrderSummaryOut(
            id=updated_order.id,
            preview_id=updated_order.preview_id,
            status=updated_order.status,
            total_inr=governance_service._paise_to_inr(updated_order.total_paise),
            currency=updated_order.currency,
            created_at=updated_order.created_at.isoformat(),
            items_count=len(snapshot.get("items", [])),
            quote_snapshot=snapshot,
        )
    except GovernanceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/audit-events", response_model=List[AuditEventOut])
def get_audit_events(
    member: FamilyMember = Depends(get_current_family_member),
    db: Session = Depends(get_db),
):
    """Retrieve audit events related to the family member's linked elder."""
    events = (
        db.query(AuditEvent)
        .order_by(AuditEvent.created_at.desc())
        .limit(25)
        .all()
    )
    out = []
    for ev in events:
        details = json.loads(ev.details_json) if ev.details_json else {}
        out.append(
            AuditEventOut(
                id=ev.id,
                actor_type=ev.actor_type,
                action=ev.action,
                target_type=ev.target_type,
                target_id=ev.target_id,
                created_at=ev.created_at.isoformat(),
                details=details,
            )
        )
    return out
