"""Database schema creation and initial seeding."""

from backend.app.db.session import engine, Base, SessionLocal
from backend.app.db.models import ElderProfile, FamilyMember
from backend.app.core.security import hash_password


def init_db() -> None:
    """Create all tables and seed default fixtures if not present."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if default elder exists
        elder = db.query(ElderProfile).filter(ElderProfile.id == "eld_demo_ramesh").first()
        if not elder:
            elder = ElderProfile(
                id="eld_demo_ramesh",
                display_name="Ramesh Sharma (Dadaji)",
                phone_number="+919876543210",
                preferred_language="hi",
                delivery_address="B-402, Shanti Vihar, Vasant Kunj, New Delhi - 110070",
                spending_limit_paise=150000,  # ₹1,500
                family_approval_required=True,
                notification_consent=True,
                is_active=True,
            )
            db.add(elder)
            db.commit()

        # Check if default family member exists
        family = db.query(FamilyMember).filter(FamilyMember.username == "priya_sharma").first()
        if not family:
            family = FamilyMember(
                id="fam_demo_priya",
                elder_profile_id="eld_demo_ramesh",
                username="priya_sharma",
                password_hash=hash_password("DemoFamily2026!"),
                full_name="Priya Sharma (Daughter)",
                role="guardian",
                phone_number="+919812345678",
                notification_channel="mock",
                consent_granted=True,
                is_active=True,
            )
            db.add(family)
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
