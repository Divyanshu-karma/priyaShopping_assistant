# Phase 2 Baseline Inspection Note

Date: 2026-10-29
Environment: `tm_project_v2` (Python 3.12.13)
Project Root: `E:\priyaShopping_assistant`

---

## 1. File Tree & Workspace State

- `.env` — Verified present. Untouched, unread, unprinted.
- `.gitignore` — Standard gitignore protecting `.env`, Python cache, and test artifacts.
- `requirements.txt` — Documents direct dependencies.
- `README.md` — Phase 1 local architecture and run instructions.
- `PHASE_1_CODING_AGENT_INSTRUCTIONS.md` — Phase 1 specifications.
- `PHASE_2_CODING_AGENT_INSTRUCTIONS.md` — Phase 2 specifications.
- `backend/app/`
  - `__init__.py`
  - `main.py`
  - `schemas.py`
  - `catalogue.py`
  - `services/orders.py`
  - `static/index.html`, `static/styles.css`, `static/app.js`
- `backend/tests/`
  - `__init__.py`
  - `test_api.py`
- `docs/BOLNA_FUNCTION_TOOL.md` — Documented contract for Bolna agent `Priya` (ID: `147b08b9-a634-4982-a8cf-a9f3d293dac5`).

---

## 2. Dependency Availability in `tm_project_v2`

The following packages were inspected in `tm_project_v2` using read-only spec checks:

| Package | Status | Notes |
|---|---|---|
| `fastapi` | Available (True) | Web framework |
| `uvicorn` | Available (True) | ASGI server |
| `pydantic` | Available (True) | Data validation |
| `pytest` | Available (True) | Testing framework |
| `httpx` | Available (True) | Test client & async HTTP |
| `sqlalchemy` | Available (True) | ORM and DB toolkit |
| `psycopg` | Available (True) | PostgreSQL v3 driver |
| `psycopg2` | Available (True) | PostgreSQL v2 driver |
| `asyncpg` | Available (True) | Async PostgreSQL driver |
| `alembic` | Available (True) | DB migration framework |
| `sqlite3` | Available (True) | Standard library local DB |
| `dotenv` | Available (True) | Environment variable reader |
| `playwright` | Missing (False) | Not installed in environment |
| `plivo` | Missing (False) | Not installed in environment |
| `passlib` | Missing (False) | Not installed in environment |
| `bcrypt` | Missing (False) | Not installed in environment |
| `argon2` | Missing (False) | Not installed in environment |
| `itsdangerous` | Missing (False) | Not installed in environment |

**Decision on missing packages:**
- For database: `sqlalchemy` + `sqlite3` are available for local persistence; `psycopg`/`psycopg2` are available for production PostgreSQL.
- For hashing & tokens: Python standard library `hashlib.pbkdf2_hmac` and `secrets` provide cryptographically secure password hashing and session tokens with zero extra dependencies and zero risk to the environment.
- For Plivo & telephony: Official Plivo integration with Bolna is directly routed from Plivo to Bolna in the cloud, so no local Plivo SDK is required.
- For browser shopping: A constrained, allowlisted mock/browser adapter interface (`ProductSource` and `BrowserShoppingAdapter`) will be implemented with local fixtures, ensuring safe execution without requiring unapproved packages.

---

## 3. Baseline Test Results

Command:
```powershell
python -m pytest backend/tests -v
```
Result: **16 passed in 2.79s (100% pass rate)**.
- Health endpoint, product search, filters, empty results, product detail, 404s, order previews, explicit confirmation, duplicate confirmation rejection (409), and order retrieval are fully functional.
