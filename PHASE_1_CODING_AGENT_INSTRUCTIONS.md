# Priya Shopping Assistant — Phase 1 Coding-Agent Instructions

**Project location:** `E:\priyaShopping_assistant`  
**Phase:** 1 of 2 — Local, end-to-end MVP  
**Primary backend:** Python + FastAPI  
**Initial catalogue/order storage:** in-memory demo data only  
**Frontend:** simple responsive HTML, CSS, and JavaScript served by FastAPI  
**Voice platform:** existing Bolna agent `Priya`; integration-ready API contract, with no live-agent changes in this phase

---

## 1. Your role and overall objective

Act as the implementation engineer. Inspect the current project, implement Phase 1 in the existing project folder, run the available checks, and report verifiable results. Do not merely provide a plan or code snippets: create the working files and test them where the installed environment permits.

Build the smallest reliable vertical slice of **Priya**, a voice-first shopping assistant intended to help elderly people in India shop through natural Hindi, English, or Hinglish conversations. Phase 1 must give us:

1. A local web page for testing the shopping flow.
2. A FastAPI backend with clean request/response schemas.
3. A clearly labelled mock catalogue with searchable products.
4. An order preview and an explicit-confirmation step.
5. A temporary in-memory order implementation behind service functions, so it can later be replaced by persistent storage without rewriting the API contract.
6. A documented Bolna custom-function integration contract that can be connected when the backend has a safe, reachable HTTPS deployment.
7. Automated or repeatable tests and exact run instructions.

The result must be a working **local demo**, not a production e-commerce system. Do not claim that any real marketplace was queried or any real order was placed.

## 2. Non-negotiable safety and workspace constraints

### 2.1 Preserve the existing `.env` and Bolna key

The project already contains `E:\priyaShopping_assistant\.env`, with a Bolna API key stored in a variable resembling `bolna_key=...`.

- **Never open and print the `.env` contents in terminal output, logs, test reports, screenshots, or your final response.** You may verify that the file exists without showing its contents.
- **Do not edit, replace, rename, move, delete, truncate, or regenerate `.env`.** Do not append configuration to it in Phase 1.
- Do not copy the key to source code, frontend code, documentation, test fixtures, command history, or another file.
- Do not echo, decode, print, or transmit the key. Do not make Bolna API calls in Phase 1.
- The Phase 1 local demo does not need the Bolna API key at runtime. Leave it unused.
- Add `.env` to `.gitignore` if not already ignored, but preserve all existing `.gitignore` content and add only missing rules.
- A `.env.example` may be created only if genuinely useful; it must contain placeholder names/values only, never the real key. Prefer not to introduce it unless needed.

### 2.2 Absolutely no changes to the Conda environment

Use the user's existing environment when working with Python:

```powershell
Set-Location 'E:\priyaShopping_assistant'
conda activate tm_project_v2
```

The existing environment is `tm_project_v2`. It already contains many libraries and tools. Treat it as **read-only**.

**Forbidden environment operations:**

- Do not run `pip install`, `python -m pip install`, `conda install`, `mamba install`, or any other package-install command.
- Do not update, upgrade, downgrade, remove, uninstall, or otherwise mutate packages.
- Do not edit the Conda environment, its configuration, or its package files.
- Do not create or switch to a different Conda environment as a workaround without asking the user first.
- Do not install missing libraries globally or into `base`.
- Do not run a dependency installation from `requirements.txt`.

First inspect availability read-only, for example by checking Python's version and import availability for `fastapi`, `uvicorn`, `pydantic`, and—if tests need them—`pytest` and `httpx`. If a required package is missing, do not install it. Continue with implementation where feasible, identify the exact missing dependency, and clearly mark which checks could not run. Ask for approval before proposing any environment change. Do not falsely report a test as passed when it could not run.

### 2.3 Protect existing project files and user data

- Work only inside `E:\priyaShopping_assistant` unless a tool or temporary test requires a clearly scoped temporary directory.
- Start by listing the top-level entries and checking filenames only. Do not dump `.env` content.
- Do not assume the directory is empty: inspect before creating or editing files.
- Preserve every existing file unless a change is essential to Phase 1. Do not delete files, reset Git, clean untracked files, or overwrite user work.
- Do not run destructive commands such as `git clean`, `git reset --hard`, `git checkout --`, `Remove-Item -Recurse`, `rmdir`, or broad deletion commands.
- Do not create a Git commit, push, deploy, or publish anything unless separately instructed.
- Make only the smallest necessary changes. If an existing file conflicts with this specification, preserve it and report the conflict rather than deleting or wholesale replacing it.

## 3. Phase 1 boundaries

### In scope

- Local FastAPI service.
- Mock catalogue with realistic but explicitly fictional demo data.
- Product search and product detail endpoints.
- Order preview, explicit demo-order confirmation, cancellation if straightforward, and retrieval of a demo order.
- In-memory data behind separable catalogue/order service modules.
- Browser frontend served by the same FastAPI application.
- Large readable text, high contrast, simple layout, accessible labels, clear loading/empty/error states.
- Local tests, API documentation through FastAPI's built-in OpenAPI page, README, and a Bolna tool contract document.
- Bolna-aware request/response design and setup instructions for a later live connection.

### Out of scope — reserve for Phase 2

- PostgreSQL, SQLite, Redis, or any persistent database.
- Family dashboard, authentication/roles, elder profiles, saved addresses, spending limits, family approvals, or notification workflows.
- Real retailer/marketplace, ONDC, payment, shipping, inventory, or order-placement integration.
- Production deployment, domain name, TLS termination, public tunnel, ngrok, port forwarding, firewall changes, or exposing the laptop to the internet.
- Purchasing/provisioning a phone number, changing call routing, or enabling live inbound/outbound calling.
- Editing the live Bolna agent, replacing its prompt, modifying its voice/language/transcriber settings, or adding a function tool through the Bolna API.
- Any claim that Priya can currently search real products or place real orders.

If Phase 1 implementation appears to require an out-of-scope activity, stop before doing it and report the blocker. Do not silently expand scope.

## 4. Architecture to implement

Use the following minimum architecture. Keep the backend small and modular; do not add microservices, a separate Node.js frontend build, an ORM, or unnecessary frameworks.

```text
E:\priyaShopping_assistant\
├── .env                              # EXISTING: preserve exactly; never print or modify
├── .gitignore                        # preserve existing entries; add missing ignore rules only
├── README.md                         # local setup, run, tests, limitations
├── requirements.txt                  # documentation of direct Python dependencies only; never install from it
├── backend\
│   ├── app\
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app, routers/endpoints, static page mounting
│   │   ├── schemas.py                # Pydantic request/response models
│   │   ├── catalogue.py              # fictional in-memory catalogue and search logic
│   │   ├── services\
│   │   │   ├── __init__.py
│   │   │   └── orders.py              # in-memory order preview/confirmation business logic
│   │   └── static\
│   │       ├── index.html             # local demo interface
│   │       ├── styles.css
│   │       └── app.js
│   └── tests\
│       ├── __init__.py
│       └── test_api.py               # available API/unit tests
└── docs\
    └── BOLNA_FUNCTION_TOOL.md         # API contract + future integration instructions
```

You may make a small, justified adjustment to this structure if it materially improves compatibility with the packages already installed. Document the adjustment. Do not add a separate frontend framework or package manager for this MVP; use the browser's native HTML/CSS/JavaScript and serve it from FastAPI. This avoids introducing Node.js dependencies and keeps the local demo simple.

### Design principle: stable interface, temporary implementation

Treat FastAPI route contracts and Pydantic schemas as the stable boundary. Treat the in-memory catalogue/order store as a replaceable demo adapter. Keep route handlers thin: validate input, call service functions, and return typed responses. Do not spread catalogue or order business logic through the frontend or directly throughout route handlers.

Do not introduce a database interface abstraction so complex that it serves no Phase 1 purpose. Simple service functions and clearly isolated in-memory data are sufficient.

## 5. Priya's product and conversation behaviour

The application is for elderly callers in India. Product descriptions and statuses must be clear and respectful. Priya should be able to support Hindi, English, or Hinglish; the local frontend may use a simple Hindi/English interface toggle or bilingual labels where practical.

The backend must return facts and structured results, not generated claims. Priya must:

- Search only the supplied mock catalogue in Phase 1.
- Show no more than three best-matching products by default, with an explicit way to request more if simple to implement.
- Report name, price, category, short description, stock/demo availability, and relevant details only when present in the data.
- Say when no matches exist; never invent a product, price, discount, stock status, warranty, or delivery promise.
- Clarify ambiguous requests rather than treating guesses as facts. For example, “number 3” must not automatically become a prescription strength or a particular product.
- Avoid pressure, urgency tactics, or steering the caller toward the most expensive item.
- Show prominently that catalogue data is fictitious demo data.

Include a small, varied mock catalogue—for example, reading glasses, a mobile phone, shoes, clothing, and groceries. All names, prices, categories, stock values, and descriptions are sample data. Put the demo-data warning in the UI, API documentation, and README. Keep prices numeric in API responses, with a currency field (`INR`) so the frontend can format them consistently as rupees.

## 6. API contract

Use a consistent `/api/v1` prefix for application endpoints. Choose the exact response fields and document them. All request bodies must be validated with Pydantic. Use predictable error responses and appropriate HTTP status codes. Do not leak stack traces, environment values, API keys, or local filesystem paths to API clients.

Implement at least these endpoints:

### `GET /api/v1/health`

Returns a lightweight health response, for example:

```json
{
  "status": "ok",
  "mode": "demo",
  "catalogue_source": "in_memory",
  "orders_persistent": false,
  "live_commerce_enabled": false
}
```

Do not claim that Bolna is connected unless a real, tested connection exists. It is acceptable to omit a Bolna-connected field altogether.

### `POST /api/v1/products/search`

Request fields:

- `query`: required, trimmed, non-empty text with a reasonable maximum length.
- `category`: optional.
- `max_price`: optional non-negative numeric value in INR.
- `limit`: optional, bounded to a small safe range, default 3.

Return a stable JSON response containing the normalized query, matches, count, `currency: "INR"`, and `demo_data: true`. Match query text against available product names, descriptions, and categories case-insensitively. Apply category and maximum-price filters when supplied. If no products match, return an empty list rather than inventing results. No network search is required.

### `GET /api/v1/products/{product_id}`

Return a single known product. Return 404 for an unknown ID.

### `POST /api/v1/orders/preview`

Accept one or more selected product IDs and positive integer quantities. Reject invalid or unknown products and quantities outside a sensible configured limit. Calculate line totals and the grand total on the backend; never trust totals supplied by the browser. Return:

- a unique preview ID;
- item/product IDs, names, unit prices, quantities and line totals;
- subtotal and total, in INR;
- `status: "awaiting_confirmation"`;
- `demo_order: true` and a clear statement that this is not a real marketplace order.

Do not invent delivery fees or shipping promises. If the demo uses a delivery fee, define it explicitly as fictional configuration; preferably keep Phase 1 totals limited to the mock items and label this clearly.

### `POST /api/v1/orders/confirm`

Require a valid preview ID and an explicit confirmation field that must be `true`. If confirmation is missing or false, do not create a confirmed order. Check that the preview exists and is still pending. A confirmed preview must not produce duplicate orders if the request is repeated. Return a demo order reference and `status: "confirmed_demo"`, with clear wording that no real order/payment was made.

The web UI must make the user actively click a clearly labelled **Confirm demo order** button after reviewing the preview. Do not preselect or automatically trigger confirmation. The preview must show product names, quantities, prices, and total before confirmation.

This confirmation endpoint is strictly for demo state. Do not connect it to a retailer, payment provider, delivery company, or other external side effect. If the voice tool contract documents a future verbal-confirmation flow, it must instruct the agent to obtain clear affirmative confirmation from the caller before calling this endpoint. A tool response alone is not evidence that a real transaction occurred.

### `GET /api/v1/orders/{order_id}`

Return an order created by the in-memory demo flow, or 404 if it is unknown. Do not imply that an order survives server restart.

### Error semantics

Use 400/422 for invalid inputs as appropriate, 404 for unknown product/preview/order IDs, and 409 for attempts to confirm a preview that is already confirmed or no longer pending. Return concise, non-sensitive error details. Never silently convert invalid data to another product/quantity.

## 7. In-memory demo implementation

- Keep the mock catalogue in `catalogue.py` or a small adjacent data module; use stable demo product IDs.
- Keep order/preview logic in `services/orders.py`.
- Make it easy to reset by restarting the local server. This is acceptable and expected in Phase 1.
- Avoid unsafe shared mutable state where unnecessary. For this single-process local demo, a simple in-memory store is sufficient; document that it is not production-grade and does not persist.
- Use backend-calculated monetary values consistently. Avoid floating-point arithmetic for money; use `Decimal` or integer paise internally and serialize values predictably as numeric INR amounts.
- Do not add a real payment flow or collect payment credentials.

## 8. Frontend requirements

Build a clean single-page local test UI served from FastAPI at `/`.

It must include:

1. A clear header: **Priya Shopping Assistant — Local Demo**.
2. A visible warning: **Demo only — products, prices, availability, and orders are sample data. No real order or payment will be made.**
3. A search field, search button, optional category/price filters if uncomplicated, and example queries such as “reading glasses under ₹500”.
4. Product result cards with name, category, short description, INR price, availability and a quantity selector/add-to-preview control.
5. A cart/order-preview area with editable quantities or a safe way to remove items.
6. A preview summary with line totals and grand total.
7. Separate buttons for **Review order**, **Confirm demo order**, and **Cancel/clear** as appropriate. The confirmation action must require an intentional click and must not be triggered by a search or preview action.
8. Visible loading, empty-results, success and error states. Disable buttons while a request is in progress to reduce duplicate submissions.
9. Readable typography, generous spacing, keyboard accessibility, proper form labels, responsive layout, and good contrast. Design for older users; do not rely on colour alone to communicate state.
10. No real personal data collection. Do not request phone number, address, date of birth, payment data, passwords, OTPs, CVV, or UPI PIN.

Use only native HTML/CSS/JavaScript. Render API-provided text safely; do not inject user query or product text using unsafe `innerHTML`. Prefer creating elements and assigning `textContent` where dynamic text is displayed. The frontend must call the local backend, not maintain its own separate catalogue or authoritative prices.

Do not add a separate login page or dashboard in Phase 1.

## 9. Bolna integration readiness

The existing Bolna agent is named `Priya`, with Agent ID:

`147b08b9-a634-4982-a8cf-a9f3d293dac5`

Treat this as configuration information, not as a reason to call the Bolna API. **Do not modify the live agent or use the Bolna key in Phase 1.**

Create `docs/BOLNA_FUNCTION_TOOL.md` that documents:

- The backend endpoint that a future Bolna custom function should call for product search (`POST /api/v1/products/search`).
- Exact request/response examples and a precise function name/description/schema suitable for manual configuration in Bolna's Tools/Function Calling interface.
- The need for a publicly reachable HTTPS endpoint before Bolna's hosted service can call the laptop's API. `localhost` and `127.0.0.1` are not reachable from Bolna's service.
- That no tunnel, public deployment, port-forwarding, or firewall changes are part of Phase 1.
- A future secure authentication approach for a deployed endpoint, with secrets kept server-side and excluded from source control. Do not reuse or expose the Bolna API key as the backend's public tool secret.
- How to manually test the function after a safe HTTPS endpoint is available.
- The clear limitation that the local demo is not yet connected to a live voice call.

Use the current official Bolna docs for function calling when documenting future setup: https://www.bolna.ai/docs/tool-calling/introduction and the API overview at https://www.bolna.ai/docs/api-reference/introduction. Do not assume undocumented API payloads or attempt to automate dashboard changes.

The Phase 1 code should have a clear, stable API contract that is suitable for Bolna to call later. It must not pretend that the connection is already active.

## 10. Security and reliability requirements

- Bind the development server to `127.0.0.1`, not `0.0.0.0`.
- Do not enable wildcard public CORS. Since the local frontend is served by the same FastAPI app, CORS should not be necessary.
- Do not expose a public tunnel or deploy the service.
- Do not log request headers containing secrets or print `.env` contents.
- Do not place any secrets in JavaScript, HTML, CSS, API responses, or the README.
- Set reasonable maximum lengths and ranges for user input, query length, `limit`, quantity, and number of line items.
- Treat all browser input as untrusted and validate it in the backend.
- Use HTTP status codes and structured response models consistently.
- Keep exception messages user-safe. Log only non-sensitive diagnostic details when needed.
- Avoid unnecessary dependencies and avoid external network calls for the local demo.
- The built-in FastAPI `/docs` and `/openapi.json` may be used for local testing.

## 11. Read-only environment preflight and implementation workflow

Follow this order. Do not skip inspection.

### Step A — Inspect safely

From PowerShell:

```powershell
Set-Location 'E:\priyaShopping_assistant'
conda activate tm_project_v2
Get-Location
Get-ChildItem -Force | Select-Object Name, Mode, Length
python --version
python -c "import importlib.util as u; print({n: u.find_spec(n) is not None for n in ['fastapi','uvicorn','pydantic','pytest','httpx']})"
```

Do not run a command that prints `.env`. Check whether `.env` exists without opening its contents. Inspect any existing source/config files before modifying them. Read-only Git status may be used if Git is already initialized; do not modify Git state.

### Step B — Implement incrementally

1. Record which relevant packages are already available; do not install anything.
2. Create the smallest architecture described above, preserving existing files.
3. Implement typed schemas and the in-memory catalogue.
4. Implement search/product-detail endpoints.
5. Implement preview/confirmation/retrieval service and endpoints, including duplicate-confirmation protection.
6. Build the static frontend and connect it to the API.
7. Write tests for matching/filtering, empty results, invalid product IDs, price totals, invalid quantities, preview state, explicit confirmation, duplicate confirmation, and unknown order IDs.
8. Create README and Bolna tool contract documentation.
9. Add only missing `.gitignore` entries; do not modify `.env`.

### Step C — Test using only installed tools

- Use existing testing tools if available. FastAPI's `TestClient` typically depends on `httpx`; check availability first.
- If the usual test tooling is missing, do not install it. Run the checks that are possible with the standard library and local server, and clearly report blocked checks.
- Run tests using the existing environment `tm_project_v2`.
- Start the server on loopback only. Verify `/api/v1/health`, `/api/v1/products/search`, an invalid product response, preview creation, missing/false confirmation rejection, successful demo confirmation, and order retrieval.
- Test the frontend manually in the browser where available. Confirm that network/API errors are visible and that a normal search never confirms an order.
- Stop only the development server process you started. Do not terminate unrelated processes.

Example local run command (run from the `backend` folder and only if the already-installed `uvicorn` is available):

```powershell
Set-Location 'E:\priyaShopping_assistant\backend'
conda activate tm_project_v2
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/` and `http://127.0.0.1:8000/docs` in the browser.

Do not run package-install commands if the example fails. Report the exact missing package or incompatibility and wait for approval before environment changes.

## 12. Phase 1 acceptance criteria

Phase 1 is complete only when all feasible criteria below are either verified as passing or transparently reported as blocked by the read-only environment constraint:

- [ ] The existing `.env` remains present and untouched; its contents and API key have never been printed or copied.
- [ ] The Conda environment `tm_project_v2` has not been modified; no package installation, update, uninstall, or environment creation occurred.
- [ ] No files were deleted and no unrelated files were overwritten.
- [ ] FastAPI starts locally on `127.0.0.1` when installed dependencies permit.
- [ ] `GET /api/v1/health` reports demo mode and non-persistent storage accurately.
- [ ] Product search supports text query, relevant optional filters, a bounded result count, empty matches, and no fabricated results.
- [ ] Product detail correctly returns a product or 404.
- [ ] Order preview totals are calculated by the backend and clearly labelled demo-only.
- [ ] Confirmation requires explicit affirmative input, a pending preview, and no duplicate order is created on repeated confirmation.
- [ ] Demo-order retrieval works within the current process; restart limitations are documented.
- [ ] Frontend works with the backend, is usable at desktop/mobile widths, and shows clear loading, error and empty states.
- [ ] Searching or previewing cannot accidentally confirm an order.
- [ ] The frontend contains no secrets, does not collect payment credentials, and displays the demo-data notice.
- [ ] Tests cover the critical flows and their actual result is recorded.
- [ ] README includes exact activation/run/test steps and known limitations.
- [ ] Bolna function contract is documented accurately; the live agent remains unchanged and no live connection is falsely claimed.

## 13. Required final report from the coding agent

When finished, report concisely but with evidence:

1. Files created or modified (filenames only for `.env`; do not show any contents).
2. Architecture and implemented endpoints.
3. Exact command to start the backend and local URL.
4. Exact tests run, command used, and pass/fail counts. Separate passed tests from checks blocked by missing packages.
5. Confirm explicitly: `.env` untouched; Bolna key not printed/copied; `tm_project_v2` unchanged; no packages installed; no files deleted; no public tunnel/deployment; live Bolna agent not modified.
6. Remaining Phase 1 limitations and the single most important next action.

Do not claim successful live Bolna calling, persistent storage, production readiness, real inventory, real order placement, payment, or delivery integration unless independently implemented and verified. Those are not Phase 1 deliverables.

---

## Official references

- Bolna function calling / custom API tools: https://www.bolna.ai/docs/tool-calling/introduction
- Bolna API overview and key-handling guidance: https://www.bolna.ai/docs/api-reference/introduction
- FastAPI testing guide: https://fastapi.tiangolo.com/tutorial/testing/

**End of Phase 1 instructions. Do not begin Phase 2 work until the user provides the separate Phase 2 instruction.**
