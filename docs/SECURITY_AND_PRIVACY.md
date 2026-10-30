# Security & Privacy Specification — Priya Shopping Assistant

## 1. Threat Model & Boundaries

Priya serves vulnerable users (elderly citizens) via public voice channels (telephony PSTN) and web interfaces. The application enforces defense-in-depth across the following boundaries:

```text
[ PSTN Caller / Web ] ──> [ Bolna Voice Agent ] ──> [ Authenticated Voice Tool API ]
                                                              │
                                                              ▼
                                                   [ Policy & Governance Engine ]
                                                              │
                                    ┌─────────────────────────┴────────────────────────┐
                                    ▼                                                  ▼
                          [ Persistent DB / Audit ]                         [ Constrained Read-Only Browser ]
```

---

## 2. Personal Data & Senior Citizen Privacy

- **Data Minimization:** No personal identification numbers (Aadhaar, PAN), biometric data, or financial credentials are ever requested or stored.
- **Delivery Addresses:** Stored only when explicitly entered in family oversight settings. Never disclosed over unverified voice calls.
- **Caller Authentication:** An incoming phone number is treated as a routing clue, **not as proof of identity**. Sensitive actions (address change, order cancellation, spending limit updates) are restricted to the authenticated Family Dashboard.
- **No Payment Details:** Priya never collects, prompts for, or logs credit card numbers, CVVs, expiration dates, UPI PINs, or bank OTPs.

---

## 3. Browser Shopping Adapter Defenses

The shopping adapter implements strict security controls to prevent unintended side effects:

1. **Read-Only Mode:** In Phase 2, the browser adapter is strictly read-only (`enabled=False` by default). It can only inspect product listings and prices. No cart additions, logins, or checkout controls are accessible.
2. **SSRF & Private Network Blocking:**
   - Enforces an explicit domain allowlist (`BrowserSecurityPolicy.allowed_domains`).
   - Automatically rejects loopback (`127.0.0.1`, `localhost`), link-local (`169.254.169.254`), and private networks (`10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`).
   - Rejects non-HTTPS schemes (`file:`, `data:`, `ftp:`, `javascript:`).
3. **Prompt Injection Mitigation:**
   - Web page content (descriptions, reviews, hidden text) is treated as untrusted data.
   - Text is sanitized via `sanitize_page_text()`, stripping prompt-injection keywords (`ignore previous instructions`, `system override`, etc.).
   - Page text is never fed into model tool-selection prompts.

---

## 4. Spending Limits & Family Approval Gates

- **Integer Paise Representation:** All financial calculations use exact integer paise (1 INR = 100 paise) or `Decimal`, eliminating floating-point rounding errors.
- **Server-Side Enforcement:** Limits and approval policies are verified on the backend, not in the browser or via LLM prompt instructions.
- **Immutable Quote Snapshots:** When an order preview is confirmed, an immutable snapshot of quoted items and prices is stored. A subsequent price change on a site cannot alter the approved quote.
- **Anti-BOLA/IDOR:** Access to elder profiles and orders requires backend ownership verification (`elder_profile_id == family_member.elder_profile_id`).

---

## 5. Secret Management & Kill Switches

- **Separation of Keys:**
  - `bolna_key` (in `.env`) is reserved exclusively for Bolna management. It is never exposed in logs or sent across API requests.
  - `PRIYA_TOOL_TOKEN` is an independent secret used to authenticate incoming tool requests from Bolna.
- **Emergency Kill Switches:**
  - `BROWSER_AGENT_ENABLED=false` (blocks all automated external browsing).
  - `NOTIFICATIONS_ENABLED=false` (blocks all external SMS/WhatsApp dispatches).
  - `LIVE_COMMERCE_ENABLED=false` (blocks all external checkout submissions).
