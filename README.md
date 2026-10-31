# Priya Shopping Assistant — Phase 2 Persistent Backend & Family Governance

Welcome to **Priya Shopping Assistant**, an accessible, voice-first shopping assistant designed to help Indian senior citizens browse, select, and order everyday items using natural Hindi, English, and Hinglish.

Phase 2 advances the project to a **persistent, secure, integration-ready vertical slice** featuring:

- **Persistent Database:** SQLite locally with zero configuration (`data/priya.db`) and PostgreSQL readiness via `DATABASE_URL`.
- **Policy & Governance:** Backend spending limit enforcement, immutable quote snapshots, and multi-tier family approval workflows.
- **Voice Tools API:** Dedicated token-authenticated Bolna endpoints (`/api/v1/voice/tools/...`).
- **Family Dashboard:** Web interface (`/dashboard`) for guardians to manage allowances, approve high-value requests, and view audit events.
- **Constrained Browser Adapter:** SSRF-protected, read-only shopping search with prompt-injection defenses.
- **Idempotent Outbox:** Transactional notification queues for family SMS/WhatsApp alerts (mock default).

> [!WARNING]
> **Demo & Mock Integration:** External marketplace checkout, live telephony calls, and external SMS/WhatsApp sends remain disabled by default until credentials, deployment domains, and explicit operator authorization are supplied.

---

## Architecture Overview

```text
E:\priyaShopping_assistant\
├── .env                              # Preserved Bolna config (read-only, untouched)
├── .gitignore                        # Git ignore rules for .env, data/, and caches
├── requirements.txt                  # Dependency specifications
├── README.md                         # Project documentation
├── backend\
│   ├── app\
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app, static mounting, routers
│   │   ├── schemas.py                # Pydantic schemas
│   │   ├── catalogue.py              # Mock catalogue products & search
│   │   ├── core\
│   │   │   ├── __init__.py
│   │   │   └── security.py           # PBKDF2 hashing & constant-time auth
│   │   ├── db\
│   │   │   ├── __init__.py
│   │   │   ├── session.py            # SQLite/PostgreSQL engine & session
│   │   │   ├── models.py             # ElderProfile, FamilyMember, OrderRecord, Audit
│   │   │   └── init_db.py            # Schema creation & default fixtures
│   │   ├── services\
│   │   │   ├── __init__.py
│   │   │   ├── orders.py             # In-memory Phase 1 order demo
│   │   │   ├── governance.py         # Persistent orders, spending limits & approvals
│   │   │   └── notifications.py      # Idempotent outbox notifications
│   │   ├── adapters\
│   │   │   ├── __init__.py
│   │   │   └── browser_shopping.py   # Allowlisted, read-only shopping adapter
│   │   ├── routers\
│   │   │   ├── __init__.py
│   │   │   ├── voice_tools.py        # Authenticated Bolna voice tools
│   │   │   └── family_dashboard.py   # Family auth, limits, approvals & audit
│   │   └── static\
│   │       ├── index.html            # Senior-accessible shopping UI
│   │       ├── styles.css            # High-contrast, large-font styles
│   │       ├── app.js                # Safe DOM JavaScript & bilingual toggle
│   │       ├── dashboard.html        # Family oversight dashboard UI
│   │       └── dashboard.js          # Family dashboard logic & approvals
│   └── tests\
│       ├── __init__.py
│       ├── test_api.py               # Phase 1 regression test suite (16 tests)
│       └── test_phase2.py            # Phase 2 persistence & governance (13 tests)
└── docs\
    ├── BOLNA_FUNCTION_TOOL.md         # Bolna custom-function tool contract
    ├── PHASE_2_BASELINE.md            # Stage 0 preflight results
    ├── PHASE_2_PROVIDER_SETUP.md      # Plivo, Bolna, and HTTPS setup guide
    ├── SECURITY_AND_PRIVACY.md        # Privacy, SSRF, and injection defenses
    └── OPERATIONS_RUNBOOK.md          # Health monitoring, backup & troubleshooting
```

---

## Local Setup & Quick Start

### 1. Activate Existing Conda Environment

```powershell
Set-Location 'E:\priyaShopping_assistant'
conda activate tm_project_v2
```

### 2. Start the Local Server

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 3. Access Web Interfaces

- **Elder Shopping Page:** 👉 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Family Oversight Dashboard:** 👉 [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)*(Pre-seeded login: `priya_sharma` / `DemoFamily2026!`)*
- **OpenAPI Documentation:** 👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Running Automated Tests

Run the complete 29-test automated test suite:

```powershell
python -m pytest backend/tests -v
```

All 29 tests pass with 100% success rate:

- 16 Phase 1 regression tests (health, search, demo preview, confirmation).
- 13 Phase 2 tests (persistence, governance, spending limits, approvals, voice tool auth, BOLA protection, SSRF blocking, prompt injection sanitization).

---

## Key API Endpoints

| Category                   | Method    | Endpoint                                           | Description                                 |
| -------------------------- | --------- | -------------------------------------------------- | ------------------------------------------- |
| **System**           | `GET`   | `/api/v1/health`                                 | Health, database mode, and subsystem status |
| **Elder Shopping**   | `POST`  | `/api/v1/products/search`                        | Search mock products                        |
| **Elder Shopping**   | `POST`  | `/api/v1/orders/preview`                         | Generate order preview                      |
| **Elder Shopping**   | `POST`  | `/api/v1/orders/confirm`                         | Explicit demo confirmation                  |
| **Voice Tools**      | `POST`  | `/api/v1/voice/tools/search_products`            | Authenticated voice search                  |
| **Voice Tools**      | `POST`  | `/api/v1/voice/tools/create_order_preview`       | Create persistent preview                   |
| **Voice Tools**      | `POST`  | `/api/v1/voice/tools/request_order_confirmation` | Explicit confirmation & policy evaluation   |
| **Voice Tools**      | `POST`  | `/api/v1/voice/tools/get_order_status`           | Order lifecycle status check                |
| **Family Dashboard** | `POST`  | `/api/v1/family/auth/login`                      | Session authentication                      |
| **Family Dashboard** | `GET`   | `/api/v1/family/profiles`                        | Authorized elder profiles                   |
| **Family Dashboard** | `PATCH` | `/api/v1/family/profiles/{id}/policy`            | Update limits & approval rules              |
| **Family Dashboard** | `GET`   | `/api/v1/family/orders`                          | Orders awaiting approval or placed          |
| **Family Dashboard** | `POST`  | `/api/v1/family/orders/{id}/approve`             | Approve order in queue                      |
| **Family Dashboard** | `POST`  | `/api/v1/family/orders/{id}/reject`              | Reject order in queue                       |
| **Family Dashboard** | `GET`   | `/api/v1/family/audit-events`                    | Security audit trail                        |
