# FarmCart Phase 2: Security & Threat Model Review

**Project:** FarmCart Direct Farm-to-Consumer Marketplace  
**Team:** Agile 11  
**Scope:** Phase 2 Security Architecture & Hardening  

---

## 1. Access Control Matrix & Authorization

FarmCart Phase 2 enforces strict role-based access control (RBAC) across all backend API routers:

| Role | Allowed Actions | Restricted Actions |
|---|---|---|
| **Buyer** | Browse produce, check PIN serviceability, place orders, cancel pending orders, confirm delivery receipt, upload dispute photo evidence, file disputes. | Cannot list produce, confirm farmer orders, resolve disputes, or access platform financial ledgers. |
| **Farmer / FPO** | Create produce listings, update inventory, view incoming produce orders, advance order status to `confirmed` and `processing`. | Cannot confirm delivery receipt, resolve buyer disputes, or alter platform fee structures. |
| **Logistics Partner** | Register fleet vehicles, view assigned batches & deliveries, advance order status to `shipped` / in-transit. | Cannot modify produce inventory, access unrelated customer details, or resolve disputes. |
| **Reviewer / Admin** | Create delivery zones & drop points, inspect all batches & cutoffs, view dispute evidence, resolve disputes (`REFUND`, `RELEASE`, `REJECTED`), inspect immutable payment ledger. | Strict dual-role separation: reviewer actions are audited with user ID and timestamp in database histories. |

---

## 2. Evidence Upload Security Hardening

To prevent Remote Code Execution (RCE), Local File Inclusion (LFI), and Server-Side Request Forgery (SSRF) via file uploads:
1. **MIME Type Whitelist:** Restricted strictly to `image/jpeg`, `image/png`, and `image/webp`. Binary executables, scripts, HTML, and PDFs are rejected with `400 Bad Request`.
2. **Extension Whitelist:** Files must end in `.jpg`, `.jpeg`, `.png`, or `.webp`.
3. **Payload Size Limit:** Strictly enforced at 5MB (`MAX_UPLOAD_SIZE_MB = 5`). Payloads exceeding this limit are terminated before writing to disk.
4. **UUID Randomization:** Uploaded files are stripped of their original client-supplied filename and renamed using a cryptographically random UUID v4 (`uuid.uuid4().hex + ext`).
5. **Private Storage:** Files are stored in a private directory (`./uploads/disputes/`) **outside the public web root** (`frontend/`). Direct file downloads are gated behind authenticated endpoints with buyer/reviewer access verification.

---

## 3. Cryptographic Signature & Webhook Verification

1. **HMAC-SHA256 Signatures:** Payment capture verification computes HMAC-SHA256 over `gateway_order_id|gateway_payment_id` using the private merchant secret.
2. **Constant-Time Comparison:** Signatures are compared using `hmac.compare_digest` to prevent side-channel timing attacks.
3. **Replay Protection:** Payments already in `paid` or `settled` state idempotently return without re-crediting or re-invoking payment capture handlers.
4. **Webhook Authenticity:** Razorpay webhooks require `X-Razorpay-Signature` validation over raw request body bytes before parsing JSON events.

---

## 4. Financial Safeguards & Anti-Fraud Gates

1. **Integer Paise Representation:** Eliminates floating-point truncation vulnerabilities.
2. **Dispute Window Strict Cutoff:** Prevents delayed fraudulent dispute submissions after 24 hours.
3. **Escrow Hold Enforcement:** Automatic escrow freeze prevents farmer payout during active disputes.
4. **Live Payout Kill-Switch:** `PAYMENT_LIVE_ENABLED=false` prevents unintended fund disbursement during testing and onboarding.

