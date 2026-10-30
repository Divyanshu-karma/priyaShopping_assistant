# Operations Runbook — Priya Shopping Assistant

## 1. Service Management

### Start Backend Service (Local Development)
```powershell
Set-Location 'E:\priyaShopping_assistant'
conda activate tm_project_v2
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Start in Production (Gunicorn / Uvicorn Workers)
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers
```

### Stop Service
- In terminal: Send `Ctrl + C` or `SIGINT`.
- In background tasks: Send `kill` signal via process manager.

---

## 2. Health & Readiness Monitoring

- **Endpoint:** `GET /api/v1/health`
- **Expected Status:** `200 OK`
- **Response Format:**
```json
{
  "status": "ok",
  "mode": "demo",
  "catalogue_source": "in_memory",
  "orders_persistent": true,
  "live_commerce_enabled": false,
  "database_mode": {
    "engine": "sqlite",
    "persistent": true,
    "is_local": true
  },
  "voice_tools_enabled": true,
  "family_dashboard_enabled": true
}
```

---

## 3. Database Maintenance & Backup

### SQLite (Local Development)
- **Path:** `data/priya.db`
- **Backup:**
  ```powershell
  Copy-Item 'data\priya.db' 'data\priya_backup_$(Get-Date -Format "yyyyMMdd").db'
  ```

### PostgreSQL (Production)
- **Backup:**
  ```bash
  pg_dump -Fc -U priya_user priya > "priya_backup_$(date +%Y%m%d).dump"
  ```
- **Restore:**
  ```bash
  pg_restore -U priya_user -d priya "priya_backup.dump"
  ```

---

## 4. Troubleshooting & Failure Recovery

| Symptom | Cause | Solution |
|---|---|---|
| `401 Unauthorized` on voice tools | Missing or incorrect `PRIYA_TOOL_TOKEN` | Verify `Authorization: Bearer <PRIYA_TOOL_TOKEN>` matches backend setting |
| `403 Forbidden` on Dashboard | BOLA/IDOR protection triggered (accessing another elder's ID) | Sign in with authorized family credentials linked to that elder |
| `409 Conflict` on Order Confirm | Duplicate confirmation or invalid state transition | Check order state in dashboard; preview is already confirmed |
| Bolna cannot reach API | Backend running on localhost/loopback | Deploy backend behind a public HTTPS reverse proxy with valid TLS |
| High-value order stuck | Awaiting family guardian approval | Log in to `/dashboard` as family guardian and click **Approve** |
