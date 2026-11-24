# FarmCart Phase 2: API Contracts & Interface Specification

**Project:** FarmCart Direct Farm-to-Consumer Marketplace  
**Team:** Agile 11  
**Status:** Implemented & Verified  

---

## 1. Nationwide Serviceability & Logistics Endpoints

### 1.1 Check PIN-Code Serviceability
- **Method:** `GET`
- **Path:** `/logistics/serviceability/{pincode}`
- **Auth:** Public / Optional
- **Response `200 OK`:**
```json
{
  "serviceable": true,
  "pincode": "560038",
  "zone_id": "z_blr_01",
  "zone_name": "Bangalore Urban Central",
  "allows_home_delivery": true,
  "allows_drop_point": true,
  "available_drop_points": [
    {
      "id": "dp_indiranagar",
      "zone_id": "z_blr_01",
      "name": "Indiranagar Metro Hub",
      "address_line": "Station Rd, Indiranagar",
      "city": "Bengaluru",
      "district": "Bangalore Urban",
      "state": "Karnataka",
      "pincode": "560038",
      "operating_hours": "08:00 - 20:00",
      "capacity_orders": 30,
      "is_active": true
    }
  ],
  "available_slots": ["morning", "afternoon", "evening"],
  "reasons": []
}
```

### 1.2 List & Create Delivery Zones
- **`GET /logistics/zones`** (Admin / Logistics): Returns array of all delivery zones.
- **`POST /logistics/zones`** (Admin): Creates a delivery zone.
  - **Request Body:**
    ```json
    {
      "name": "Bangalore North Urban",
      "state": "Karnataka",
      "district": "Bangalore Urban",
      "city": "Bengaluru",
      "serviceable_pincodes": ["560001", "560002", "560038"],
      "min_batch_threshold_kg": 25.0,
      "max_batch_weight_kg": 600.0,
      "max_batch_orders": 40,
      "preparation_buffer_hours": 4.0,
      "dispatch_buffer_hours": 1.0,
      "allows_home_delivery": true,
      "allows_drop_point": true
    }
    ```

### 1.3 List & Create Shared Drop Points
- **`GET /logistics/drop-points`** (Optional query `?zone_id=...`): Returns active pickup hubs.
- **`POST /logistics/drop-points`** (Admin):
  - **Request Body:**
    ```json
    {
      "zone_id": "z_blr_01",
      "name": "Indiranagar Community Hub",
      "address_line": "12, 100ft Road, Indiranagar",
      "city": "Bengaluru",
      "district": "Bangalore Urban",
      "state": "Karnataka",
      "pincode": "560038",
      "operating_hours": "08:00 - 20:00",
      "capacity_orders": 50
    }
    ```

### 1.4 Receiver Delivery Confirmation (Without OTP)
- **Method:** `POST`
- **Path:** `/logistics/deliveries/{id}/confirm-receipt`
- **Auth:** Bearer Token (Designated Buyer or Platform Admin)
- **Request Body:**
```json
{
  "notes": "Verified receipt at doorstep without OTP"
}
```
- **Response `200 OK`:**
```json
{
  "id": "del_123456",
  "order_id": "ord_987654",
  "status": "delivered",
  "receiver_confirmed": true,
  "confirmed_at": "2026-11-10T12:00:00Z"
}
```

### 1.5 Evaluate Schedule Cutoffs
- **Method:** `POST`
- **Path:** `/logistics/batches/evaluate-cutoffs`
- **Auth:** Bearer Token (Logistics or Admin)
- **Response `200 OK`:**
```json
{
  "evaluated_count": 5,
  "dispatched_count": 4,
  "flagged_for_review_count": 1
}
```

---

## 2. Order Processing & Lifecycle Endpoints

### 2.1 Create Order with Indian Address & Mode
- **Method:** `POST`
- **Path:** `/orders`
- **Auth:** Bearer Token (`buyer` role)
- **Request Body:**
```json
{
  "order_type": "individual",
  "delivery_mode": "home_delivery",
  "delivery_location": "Flat 302, Green Glen Layout, Bellandur",
  "pincode": "560103",
  "shared_drop_point_id": null,
  "delivery_slot": "2026-12-01|morning",
  "items": [
    { "produce_id": "prod_1", "quantity": 10.0 }
  ]
}
```

### 2.2 Get Detailed Order Tracking
- **Method:** `GET`
- **Path:** `/orders/{id}/tracking`
- **Auth:** Authenticated User
- **Response `200 OK`:**
```json
{
  "order_id": "ord_987654",
  "status": "delivered",
  "delivery_mode": "home_delivery",
  "is_serviceable": true,
  "delivered_at": "2026-11-10T10:00:00Z",
  "receiver_confirmed_at": "2026-11-10T10:15:00Z",
  "dispute_eligible": true,
  "dispute_window_expires_at": "2026-11-11T10:00:00Z",
  "active_dispute": null,
  "payment_status": "awaiting_buyer_confirmation",
  "payment_held": false
}
```

### 2.3 Transition Order Status
- **Method:** `POST`
- **Path:** `/orders/{id}/status`
- **Auth:** Bearer Token (Role-checked)
- **Request Body:**
```json
{
  "status": "confirmed",
  "reason": "Farmer confirmed stock packaging"
}
```

### 2.4 Cancel Order
- **Method:** `POST`
- **Path:** `/orders/{id}/cancel`
- **Auth:** Bearer Token (Buyer or Admin)
- **Request Body:**
```json
{
  "reason": "Ordered wrong product by mistake"
}
```

---

## 3. Dispute Management Endpoints

### 3.1 File Delivery Dispute
- **Method:** `POST`
- **Path:** `/disputes`
- **Auth:** Bearer Token (Designated Buyer)
- **Request Body:**
```json
{
  "order_id": "ord_987654",
  "reason": "DAMAGED_PRODUCE",
  "description": "Apples arrived crushed and rotting in packaging box."
}
```
- **Response `201 Created`:**
```json
{
  "id": "disp_abc123",
  "order_id": "ord_987654",
  "buyer_id": "bp_buyer1",
  "reason": "DAMAGED_PRODUCE",
  "description": "Apples arrived crushed and rotting in packaging box.",
  "status": "OPEN",
  "evidence": []
}
```

### 3.2 Upload Dispute Photo Evidence
- **Method:** `POST`
- **Path:** `/disputes/evidence/upload`
- **Content-Type:** `multipart/form-data`
- **Auth:** Bearer Token (Buyer or Admin)
- **Parameters:**
  - `file`: Image file (JPEG, PNG, WebP — max 5MB)
- **Response `200 OK`:**
```json
{
  "url": "/disputes/evidence/ev_12345/file",
  "file_name": "damaged_apples.jpg",
  "mime_type": "image/jpeg",
  "size_bytes": 1024500
}
```

### 3.3 Resolve Dispute (Reviewer Workflow)
- **Method:** `POST`
- **Path:** `/disputes/{id}/resolve`
- **Auth:** Bearer Token (`admin` or `reviewer` role)
- **Request Body:**
```json
{
  "decision": "REFUND",
  "notes": "Photo evidence confirms severe bruising during transit. Approved full refund."
}
```
- **Response `200 OK`:** Returns resolved `DisputeOut` schema.

---

## 4. Payment Gateway & Ledger Endpoints

### 4.1 Initiate Gateway Checkout
- **Method:** `POST`
- **Path:** `/payments/initiate`
- **Auth:** Bearer Token
- **Request Body:**
```json
{
  "order_id": "ord_987654",
  "provider": "mock"
}
```
- **Response `200 OK`:**
```json
{
  "payment_id": "pay_555",
  "order_id": "ord_987654",
  "amount_inr": 1200.0,
  "amount_paise": 120000,
  "currency": "INR",
  "gateway_provider": "mock",
  "gateway_order_id": "mock_order_998877",
  "key_id": "mock_key_id"
}
```

### 4.2 Verify Client Payment Signature
- **Method:** `POST`
- **Path:** `/payments/verify`
- **Auth:** Bearer Token
- **Request Body:**
```json
{
  "payment_id": "pay_555",
  "gateway_order_id": "mock_order_998877",
  "gateway_payment_id": "pay_mock_123",
  "gateway_signature": "a1b2c3d4e5f6..."
}
```

### 4.3 View Payment Ledger Entries (Double-Entry Audit Log)
- **Method:** `GET`
- **Path:** `/payments/ledger`
- **Auth:** Bearer Token (`admin` role)
- **Response `200 OK`:** Array of `PaymentLedgerEntryOut`.

