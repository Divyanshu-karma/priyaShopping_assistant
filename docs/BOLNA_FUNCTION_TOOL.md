# Bolna Custom-Function Tool Integration Contract (Phase 2)

This document provides the exact technical specification for connecting **Priya** (Bolna voice agent ID `147b08b9-a634-4982-a8cf-a9f3d293dac5`) to the backend via authenticated custom-function tool calling.

---

## 1. Agent Configuration & Status

- **Bolna Agent Name:** `Priya`
- **Bolna Agent ID:** `147b08b9-a634-4982-a8cf-a9f3d293dac5`
- **Phase 2 Status:** **Implementation Ready — Awaiting Deployed HTTPS Endpoint & Manual Configuration.**

> [!IMPORTANT]
> The live Bolna agent has **not been modified** via API. All tools and telephony routing are configured manually in the operator dashboard once an HTTPS endpoint is deployed.

---

## 2. Network & Public Endpoint Prerequisite

Bolna's cloud platform requires a publicly accessible HTTPS endpoint with TLS 1.2/1.3:

- Local loopback addresses (`127.0.0.1`, `localhost`) cannot be reached by Bolna's servers.
- During local testing, tool endpoints are validated via automated tests and local loopback clients using `PRIYA_TOOL_TOKEN`.
- For staging/production, configure your reverse proxy (e.g., Caddy, Nginx, or Cloud Run) to forward to FastAPI.

---

## 3. Dedicated Tool Endpoints & Authentication

All tool calls are protected by a dedicated secret bearer token:

- **Header:** `Authorization: Bearer <PRIYA_TOOL_TOKEN>`
- **Security Rule:** The Bolna management API key (`bolna_key=...` in `.env`) is strictly for platform management. It must **never** be used as the tool bearer token or transmitted over HTTP requests.

---

## 4. Bolna Tool Specifications

### Tool 1: `search_products`

- **Endpoint:** `POST https://<DEPLOYED_DOMAIN>/api/v1/voice/tools/search_products`
- **Description:** *Search for products in Priya's catalogue. Use when the caller mentions items to buy (e.g. glasses, phones, shoes, walking sticks).*
- **Parameters:**

```json
{
  "type": "object",
  "properties": {
    "query": { "type": "string", "description": "Search keyword or item name" },
    "category": { "type": "string", "description": "Optional category filter", "nullable": true },
    "max_price": { "type": "number", "description": "Budget ceiling in INR", "nullable": true },
    "limit": { "type": "integer", "description": "Max items to return (1-5)", "default": 3 }
  },
  "required": ["query"]
}
```

### Tool 2: `get_product_details`

- **Endpoint:** `POST https://<DEPLOYED_DOMAIN>/api/v1/voice/tools/get_product_details`
- **Description:** *Retrieve full description, specifications, and availability for a product.*
- **Parameters:**

```json
{
  "type": "object",
  "properties": {
    "product_id": { "type": "string", "description": "The unique product ID" }
  },
  "required": ["product_id"]
}
```

### Tool 3: `create_order_preview`

- **Endpoint:** `POST https://<DEPLOYED_DOMAIN>/api/v1/voice/tools/create_order_preview`
- **Description:** *Create an order preview with exact backend-calculated totals before seeking confirmation.*
- **Parameters:**

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "product_id": { "type": "string" },
          "quantity": { "type": "integer", "default": 1 }
        },
        "required": ["product_id"]
      }
    },
    "elder_profile_id": { "type": "string", "description": "Elder profile ID if verified", "nullable": true }
  },
  "required": ["items"]
}
```

### Tool 4: `request_order_confirmation`

- **Endpoint:** `POST https://<DEPLOYED_DOMAIN>/api/v1/voice/tools/request_order_confirmation`
- **Description:** *Submit an explicit affirmative order confirmation from the caller. Evaluates spending limits and family approval policy. Does NOT place real external marketplace orders.*
- **Parameters:**

```json
{
  "type": "object",
  "properties": {
    "preview_id": { "type": "string", "description": "The preview ID returned by create_order_preview" },
    "confirmed": { "type": "boolean", "description": "Must be true (caller explicitly agreed to exact total)" },
    "elder_profile_id": { "type": "string", "nullable": true }
  },
  "required": ["preview_id", "confirmed"]
}
```

### Tool 5: `get_order_status`

- **Endpoint:** `POST https://<DEPLOYED_DOMAIN>/api/v1/voice/tools/get_order_status`
- **Description:** *Check the current status of an order (e.g. awaiting_family_approval, approved_for_execution).*
- **Parameters:**

```json
{
  "type": "object",
  "properties": {
    "order_id": { "type": "string", "description": "Order reference ID" }
  },
  "required": ["order_id"]
}
```

---

## 5. Conversational Behavioral Guidelines for Priya

1. **Explicit Final Quote:** Priya must state the exact product name, quantity, and total in Indian Rupees (`₹`) before asking: *"Should I confirm this demo order for you?"*
2. **Never Fabricate Orders:** If an order status is `awaiting_family_approval`, Priya must say: *"Your order has been recorded and is currently waiting for approval from your family."* She must **never** claim payment has been taken or that the package is in transit.
3. **No Credential Harvesting:** Priya must never request credit card numbers, CVVs, OTPs, UPI PINs, or netbanking passwords.
