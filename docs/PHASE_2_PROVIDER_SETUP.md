# Phase 2 Provider Setup Guide (Plivo, Bolna, Notifications & HTTPS)

This document provides operator instructions for connecting telephony, cloud voice agents, and notification channels.

---

## 1. Telephony Architecture: Plivo ↔ Bolna Integration

Following [Plivo&#39;s Official Audio Streaming Integration with Bolna](https://docs.plivo.com/docs/audio-streaming/integration-guides/bolna):

```text
PSTN Caller (India)
       │
       ▼
Plivo Phone Number + Application
       │ (Answer URL points directly to Bolna webhook/stream)
       ▼
Bolna Cloud Voice Agent ("Priya" ID: 147b08b9-a634-4982-a8cf-a9f3d293dac5)
       │
       ▼ (HTTPS Tool Calls with PRIYA_TOOL_TOKEN)
FastAPI Backend (https://<your-domain>/api/v1/voice/tools/...)
```

### Operator Setup Steps:

1. **Plivo Console:**
   - Create or select an existing voice-enabled phone number.
   - For Indian phone numbers, complete required regulatory KYC documentation directly in the Plivo console.
   - Create a Plivo Application and set the **Answer URL** to Bolna's stream endpoint (provided in the Bolna dashboard).
2. **Bolna Console:**
   - Navigate to Agent **Priya** (`147b08b9-a634-4982-a8cf-a9f3d293dac5`).
   - Under **Telephony Integration**, select **Plivo**.
   - Input your Plivo Auth ID and Auth Token in the Bolna dashboard (do not commit these secrets to source code).
   - Link the Plivo phone number to the agent.

---

## 2. Public HTTPS Backend Deployment

Bolna runs in the cloud and cannot access `127.0.0.1:8000`.

### Deployment Checklist:

1. Deploy the FastAPI app using Docker or a cloud host (AWS ECS, Google Cloud Run, DigitalOcean, or a VPS).
2. Ensure valid TLS (HTTPS) with a domain name (e.g. `https://priya.example.com`).
3. Set environment variables on the host:
   ```bash
   PRIYA_TOOL_TOKEN="<generate-random-64-char-hex-token>"
   DATABASE_URL="postgresql://user:password@db-host:5432/priya" # or leave unset for SQLite
   ```
4. Verify `/api/v1/health` returns `status: "ok"`.

---

## 3. Configuring Bolna Custom Tools

In the **Bolna Agent Dashboard > Tools / Function Calling**:

1. Add custom API tool `search_products`:
   - URL: `https://<YOUR_DOMAIN>/api/v1/voice/tools/search_products`
   - Method: `POST`
   - Headers: `Authorization: Bearer <YOUR_PRIYA_TOOL_TOKEN>`
2. Add custom API tool `get_product_details`:
   - URL: `https://<YOUR_DOMAIN>/api/v1/voice/tools/get_product_details`
   - Method: `POST`
   - Headers: `Authorization: Bearer <YOUR_PRIYA_TOOL_TOKEN>`
3. Add custom API tool `create_order_preview`:
   - URL: `https://<YOUR_DOMAIN>/api/v1/voice/tools/create_order_preview`
   - Method: `POST`
   - Headers: `Authorization: Bearer <YOUR_PRIYA_TOOL_TOKEN>`
4. Add custom API tool `request_order_confirmation`:
   - URL: `https://<YOUR_DOMAIN>/api/v1/voice/tools/request_order_confirmation`
   - Method: `POST`
   - Headers: `Authorization: Bearer <YOUR_PRIYA_TOOL_TOKEN>`
5. Add custom API tool `get_order_status`:
   - URL: `https://<YOUR_DOMAIN>/api/v1/voice/tools/get_order_status`
   - Method: `POST`
   - Headers: `Authorization: Bearer <YOUR_PRIYA_TOOL_TOKEN>`

---

## 4. Notification Provider Setup

By default, the notification system runs in **Mock Mode**, writing to the `notification_outbox` table and server logs.

To enable real SMS/WhatsApp notifications in production:

1. Set runtime environment variables:
   ```bash
   NOTIFICATION_PROVIDER="sms" # or "whatsapp"
   SMS_PROVIDER_KEY="<key>"
   SMS_SENDER_ID="<sender-id>"
   ```
2. Verify explicit elder/family consent is recorded in `ElderProfile.notification_consent = True`.
3. Notifications will only be dispatched for authorized events:
   - High-value order requiring family approval.
   - Order approved/rejected by guardian.

---

## 5. Safe Smoke Testing Walkthrough

Before accepting live phone calls:

1. Issue a curl test directly against the deployed tool endpoint:
   ```bash
   curl -X POST "https://<YOUR_DOMAIN>/api/v1/voice/tools/search_products" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <PRIYA_TOOL_TOKEN>" \
     -d '{"query": "glasses", "limit": 2}'
   ```
2. In Bolna's web chat / simulator:
   - Send: *"नमस्ते प्रिया, मुझे पढ़ने का चश्मा चाहिए।"*
   - Verify Priya calls `search_products`, receives the structured items, and speaks: *"मैंने 2 चश्मे खोजे हैं..."*
3. Test approval workflow:
   - Request to buy an item over the spending limit.
   - Observe order enters `awaiting_family_approval`.
   - Log into `https://<YOUR_DOMAIN>/dashboard` as family guardian and click **Approve**.
   - Confirm status transitions to `approved_for_execution`.
