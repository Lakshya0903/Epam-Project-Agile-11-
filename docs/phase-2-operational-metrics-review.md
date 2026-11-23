# FarmCart Phase 2 — Operational Metrics & Data Quality Review
**Author:** Mansi Jain (Data Analyst + Testing Engineer, Team Agile 11)  
**Date:** November 2026  
**Status:** Approved Operational Baseline  
**Scope:** Phase 2 Nationwide Logistics, Batches, Receiver Deliveries, Disputes & Payment Escrow  

---

## 1. Executive Summary & Purpose

This document establishes the operational reporting framework and data quality benchmarks for FarmCart Phase 2. As FarmCart transitions from direct farmer-to-buyer transactions into aggregated area-based delivery batching and nationwide logistics across India, operational visibility is paramount to monitor platform health, ensure fair farmer payouts, protect buyer satisfaction, and minimize delivery SLA breaches.

This review defines ten primary operational Key Performance Indicators (KPIs), formulates their mathematical derivations, maps the required database source tables, outlines data quality constraints, and highlights observational limitations distinguishing seed/synthetic fixtures from live production workloads.

---

## 2. Operational Metrics & KPI Formulations

### 2.1 Batch Fill Rate (Weight & Order Count)
* **Definition:** The proportion of configured batch capacity consumed at the moment of batch cutoff and dispatch.
* **Calculation:**
  $$\text{Fill Rate}_{\text{weight}} = \frac{\sum \text{Order Total Weight (kg)}}{\text{DeliveryBatch.max\_weight\_kg}} \times 100\%$$
  $$\text{Fill Rate}_{\text{count}} = \frac{\text{DeliveryBatch.current\_order\_count}}{\text{DeliveryBatch.max\_orders}} \times 100\%$$
* **Primary Source Tables:** `delivery_batches`, `orders`
* **Target Operational Range:** $70\% - 95\%$ of capacity prior to dispatch.
* **Interpretation:** Batches dispatching below the configurable minimum threshold (default 25 kg / 5 orders) incur higher marginal logistics costs. Batches hitting 100% trigger automatic spillover into subsequent time slots.

### 2.2 Average Batch Weight & Order Density
* **Definition:** The average mass and order volume processed per delivery batch within a given zone and delivery slot.
* **Calculation:**
  $$\overline{W}_{\text{batch}} = \frac{\sum_{i=1}^{N} \text{batch.current\_weight\_kg}}{N}, \quad \overline{O}_{\text{batch}} = \frac{\sum_{i=1}^{N} \text{batch.current\_order\_count}}{N}$$
* **Primary Source Tables:** `delivery_batches`
* **Target Benchmark:** $\ge 35\text{ kg}$ per batch; $\ge 6\text{ orders}$ per batch in urban clusters (e.g. Bangalore East).

### 2.3 Batch Cutoff Compliance & Miss Rate
* **Definition:** Percentage of batches successfully frozen at or before their system-calculated cutoff time without emergency post-cutoff order insertions.
* **Calculation:**
  $$\text{Cutoff Compliance} = \frac{N_{\text{frozen on schedule}}}{N_{\text{total batches}}} \times 100\%$$
* **Primary Source Tables:** `delivery_batches`, `orders` (`created_at`, `cutoff_time`, `delivery_date`)
* **Threshold:** Cutoff is enforced dynamically: $4\text{ hours}$ before morning delivery slot (08:00–12:00) and $3\text{ hours}$ before afternoon slot (13:00–17:00).

### 2.4 Delivery Completion Rate (DCR)
* **Definition:** Percentage of dispatched orders successfully transitioned to `DELIVERED` status upon receiver confirmation.
* **Calculation:**
  $$\text{DCR} = \frac{N_{\text{orders with status = DELIVERED}}}{N_{\text{orders dispatched (SHIPPED)}}} \times 100\%$$
* **Primary Source Tables:** `orders`, `deliveries`
* **Target Benchmark:** $\ge 98.5\%$ completion within the promised delivery time window.

### 2.5 Delivery Delay & Latency
* **Definition:** Duration between promised delivery slot end-time and actual receiver confirmation timestamp (`deliveries.delivered_at`).
* **Calculation:**
  $$\text{Delay}_{\text{minutes}} = \max\left(0, \frac{\text{delivered\_at} - \text{slot\_end\_time}}{60\text{ seconds}}\right)$$
* **Primary Source Tables:** `deliveries`, `orders`

### 2.6 Receiver Confirmation Without OTP Adoption
* **Definition:** Percentage of deliveries confirmed via the authenticated receiver self-service web endpoint (`POST /logistics/deliveries/{id}/confirm-receipt`) vs. legacy fallback flows.
* **Calculation:**
  $$\text{Receiver Confirm Rate} = \frac{N_{\text{deliveries confirmed by buyer}}}{N_{\text{total delivered orders}}} \times 100\%$$
* **Primary Source Tables:** `deliveries.confirmed_by_id`, `deliveries.delivered_at`
* **Target Benchmark:** $100\%$ receiver confirmations recorded without requiring external SMS OTP transit.

### 2.7 Dispute Frequency (Incident Rate)
* **Definition:** Percentage of delivered orders resulting in an official buyer dispute filed within the 24-hour post-delivery window.
* **Calculation:**
  $$\text{Dispute Rate} = \frac{N_{\text{disputes filed}}}{N_{\text{total delivered orders}}} \times 100\%$$
* **Primary Source Tables:** `disputes`, `orders`, `deliveries`
* **Target Benchmark:** $\le 1.5\%$ of delivered orders across produce categories.

### 2.8 Dispute Resolution Latency & Adjudication Breakdown
* **Definition:** Mean elapsed time from dispute filing (`disputes.created_at`) to admin reviewer adjudication (`disputes.resolved_at`), categorized by resolution outcome (`RELEASE_TO_FARMER`, `FULL_REFUND`, `PARTIAL_REFUND`).
* **Calculation:**
  $$\overline{T}_{\text{resolution}} = \frac{\sum (\text{resolved\_at} - \text{created\_at})}{N_{\text{resolved disputes}}}$$
* **Primary Source Tables:** `disputes`
* **Target Benchmark:** SLA $\le 4\text{ hours}$ from submission to resolution.

### 2.9 Payment Release Delays & Escrow Hold Time
* **Definition:** Time elapsed between delivery confirmation and final fund disbursement to farmer and logistics partner accounts.
* **Calculation:**
  $$\text{Hold Time} = \text{ledger\_release\_timestamp} - \text{delivery\_confirmation\_timestamp}$$
* **Primary Source Tables:** `orders.payment_status`, `ledger_entries`, `deliveries.delivered_at`
* **Governance Rule:** Escrow holds funds for exactly $24\text{ hours}$ post-delivery (or until dispute resolution) before unlocking farmer payouts.

### 2.10 Refund Frequency & Ratio
* **Definition:** The ratio of refunded payment volume (paise) relative to total gross marketplace volume (GMV).
* **Calculation:**
  $$\text{Refund Ratio} = \frac{\sum \text{Refund Amount (paise)}}{\sum \text{Total Gross Captured (paise)}} \times 100\%$$
* **Primary Source Tables:** `payment_transactions`, `ledger_entries`
* **Financial Integrity:** Calculated in integer paise to avoid IEEE-754 floating point distortion.

---

## 3. Database Schema Entity Mapping

| KPI Category | Required Database Entities | Foreign Keys & Joins |
|---|---|---|
| **Batching & Capacity** | `delivery_batches`, `orders` | `orders.batch_id == delivery_batches.id` |
| **Logistics & Delivery** | `deliveries`, `orders`, `delivery_zones` | `deliveries.order_id == orders.id`, `orders.zone_id == delivery_zones.id` |
| **Dispute Management** | `disputes`, `dispute_evidence`, `users` | `disputes.order_id == orders.id`, `dispute_evidence.dispute_id == disputes.id` |
| **Escrow & Payments** | `payment_transactions`, `ledger_entries` | `payment_transactions.order_id == orders.id`, `ledger_entries.order_id == orders.id` |

---

## 4. Data Quality & Integrity Checks

1. **Strict Indian PIN Code Normalization:** PIN codes must conform to `^[1-9][0-9]{5}$`. Trailing or embedded spaces are sanitized prior to zone evaluation.
2. **Batch Invariant Integrity:** A batch must never have `current_weight_kg > max_weight_kg` or `current_order_count > max_orders`. Any violation triggers an immediate service alert.
3. **Canonical 5-State Progression:** Order status transitions must strictly follow `PLACED -> CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED`. Backward status jumps or duplicate deliveries are blocked at the ORM layer.
4. **Dispute Window Enforcement:** Disputes filed after `deliveries.delivered_at + 24 hours` must be rejected with HTTP 400 Bad Request.
5. **Integer Currency Integrity:** All transactional arithmetic (`amount_paise`, `farmer_share_paise`, `logistics_share_paise`, `platform_fee_paise`) must sum identically to `total_amount_paise` without rounding discrepancies.

---

## 5. Distinction Between Synthetic Fixtures and Production Telemetry

> [!NOTE]
> In current testing and local development environments, metrics are populated using automated seed fixtures (`backend/seed.py`) and simulated end-to-end integration test runs (`tests/test_phase2_workflows.py`).
>
> In production deployment:
> - Real-time metrics will be harvested via automated SQL analytical queries executed against PostgreSQL read replicas.
> - Dashboards will refresh operational summaries every 5 minutes to maintain low read latency on the primary transactional database.

---

## 6. Recommendations for Operational Readiness

1. **Deploy Materialized Analytical Views:** Create daily rollup tables in PostgreSQL for batch utilization and dispute rates to avoid executing heavy aggregation joins across `orders` and `delivery_batches`.
2. **Automated Cutoff Watcher:** Run an hourly cron task (`backend/services/batch_engine.py:freeze_expired_batches`) to auto-lock batches reaching their cutoff times.
3. **Escrow Auto-Release Job:** Run a scheduled runner that identifies deliveries older than 24 hours with no active dispute and automatically sets `orders.payment_status = COMPLETED` while writing corresponding `CREDIT` entries into `ledger_entries`.
