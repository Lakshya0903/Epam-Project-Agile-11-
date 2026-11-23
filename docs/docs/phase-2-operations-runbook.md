# FarmCart Phase 2: Operations & Maintenance Runbook

**Project:** FarmCart Direct Farm-to-Consumer Marketplace  
**Team:** Agile 11  
**Target Audience:** DevOps Engineers, Platform Administrators & Operations Reviewers  

---

## 1. Environment & Service Startup

### 1.1 Local Development Startup
```bash
# 1. Activate Virtual Environment
cd backend
.\venv\Scripts\activate

# 2. Run Database Migrations to Latest Schema
alembic upgrade head

# 3. Seed Reference Entities (Zones, Hubs, Partners, Users, Produce)
python seed.py

# 4. Launch FastAPI Service
uvicorn app.main:app --reload --port 8000
```
- Web Application: `http://localhost:8000/static/index.html`
- Interactive API Docs: `http://localhost:8000/docs`

---

## 2. Platform Administration & Operations Guide

### 2.1 Managing Delivery Zones
Administrators can register new geographic delivery zones via the Admin Dashboard or via the API:
```bash
curl -X POST http://localhost:8000/logistics/zones \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pune South Urban",
    "state": "Maharashtra",
    "district": "Pune",
    "city": "Pune",
    "serviceable_pincodes": ["411001", "411002", "411038"],
    "min_batch_threshold_kg": 25.0,
    "max_batch_weight_kg": 500.0,
    "max_batch_orders": 50,
    "preparation_buffer_hours": 4.0,
    "dispatch_buffer_hours": 1.0,
    "allows_home_delivery": true,
    "allows_drop_point": true
  }'
```

### 2.2 Adding Shared Drop Points
```bash
curl -X POST http://localhost:8000/logistics/drop-points \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": "<ZONE_ID>",
    "name": "Swargate Collection Hub",
    "address_line": "Near Metro Station, Swargate",
    "city": "Pune",
    "district": "Pune",
    "state": "Maharashtra",
    "pincode": "411042",
    "operating_hours": "08:00 - 20:00",
    "capacity_orders": 40
  }'
```

### 2.3 Evaluating Delivery Batches & Schedule Cutoffs
To evaluate active batches against their delivery cutoff schedules:
- Via Admin Dashboard: Navigate to **"Batches Monitor"** tab and click **"Evaluate Schedule Cutoffs"**.
- Via API / Cron:
  ```bash
  curl -X POST http://localhost:8000/logistics/batches/evaluate-cutoffs \
    -H "Authorization: Bearer <LOGISTICS_OR_ADMIN_TOKEN>"
  ```
  Batches meeting minimum threshold are auto-dispatched to assigned fleet partners. Batches failing threshold are flagged for manual operator override.

---

## 3. Customer Dispute Resolution Runbook

When a buyer reports damage, spoilage, or missing produce within 24 hours of delivery:
1. Log in with `reviewer` or `admin` credentials:
   - Default Seed Reviewer: `reviewer@farmcart.test` / `ReviewerPass123!`
2. Navigate to the **"Disputes Review"** tab on the Admin Dashboard.
3. Review the reported claim:
   - Click on photo evidence thumbnails to inspect high-resolution images.
   - Read the buyer's detailed problem statement.
   - Verify order contents, delivery timestamp, and transit duration.
4. Submit resolution with mandatory justification notes:
   - **Approve Full Refund (`REFUND`):** Payment status changes to `refunded`, refund is recorded on ledger, and funds are scheduled for client refund.
   - **Authorize Farmer Release (`RELEASE`):** Dismisses claim if damage is within acceptable cosmetic tolerance; releases hold for payout.
   - **Reject Dispute (`REJECTED`):** Rejects invalid, fraudulent, or unsubstantiated claims.

---

## 4. Payment Gateway Onboarding & Live Transition

By default, FarmCart runs in **Mock Provider** mode for zero-credential development and automated testing.

### Transitioning to Razorpay Sandbox
1. Update `backend/.env`:
   ```env
   PAYMENT_PROVIDER=razorpay
   PAYMENT_MODE=sandbox
   PAYMENT_KEY_ID=rzp_test_YourTestKeyId
   PAYMENT_KEY_SECRET=YourTestKeySecret
   PAYMENT_WEBHOOK_SECRET=YourWebhookSecret
   ```
2. Restart backend server.
3. Verify client checkout transactions via Razorpay Test Dashboard.

### Transitioning to Live Production
1. Obtain verified Razorpay live merchant credentials (`rzp_live_...`).
2. Update `backend/.env`:
   ```env
   PAYMENT_PROVIDER=razorpay
   PAYMENT_MODE=live
   PAYMENT_KEY_ID=rzp_live_YourLiveKeyId
   PAYMENT_KEY_SECRET=YourLiveKeySecret
   PAYMENT_WEBHOOK_SECRET=YourLiveWebhookSecret
   PAYMENT_LIVE_ENABLED=true
   ```
3. Configure the webhook endpoint in your Razorpay Merchant Portal:
   - URL: `https://your-domain.com/payments/webhooks/razorpay`
   - Secret: Matches `PAYMENT_WEBHOOK_SECRET`
   - Active Events: `payment.captured`, `payment.failed`, `refund.processed`

