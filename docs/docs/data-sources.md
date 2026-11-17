# Research Report: Verifiable Indian Mandi Price Data Sources

## 1. Executive Summary

A critical value driver for FarmCart is providing farmers with benchmark market prices so they can list produce at competitive, fair rates. This document details verifiable government and institutional data sources in India, their API schemas, update cadences, integration risks, and recommended consumption patterns for the platform.

---

## 2. Primary Government Data Sources

### A. Open Government Data (OGD) Platform India (`data.gov.in`)
- **Portal URL**: [https://data.gov.in/](https://data.gov.in/)
- **Primary Resource**: *Current Daily Price and Arrival of Agricultural Commodities in Markets (Mandis)*
- **API Endpoint Structure**:
  `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070?api-key=YOUR_API_KEY&format=json&limit=100`
- **Data Attributes Provided**:
  | Attribute Name | Data Type | Description | Example |
  |---|---|---|---|
  | `state` | String | State name | "Maharashtra" |
  | `district` | String | Administrative district | "Nashik" |
  | `market` | String | Registered APMC mandi name | "Lasalgaon" |
  | `commodity` | String | Agricultural commodity | "Onion" |
  | `variety` | String | Sub-variety / cultivar | "Red Onion" |
  | `arrival_date` | Date (DD/MM/YYYY) | Date of recorded arrival | "02/11/2026" |
  | `min_price` | Numeric | Lowest traded price (INR / Quintal) | 1800 |
  | `max_price` | Numeric | Highest traded price (INR / Quintal) | 2600 |
  | `modal_price` | Numeric | Most frequent transaction price (INR / Quintal) | 2250 |
- **Availability & Cadence**: Updated daily between 18:00 and 22:00 IST as APMC returns are filed.
- **Access Model**: Free developer API key from data.gov.in with a limit of 10,000 requests/day.

---

### B. Agmarknet (Agricultural Marketing Information Network)
- **Portal URL**: [https://agmarknet.gov.in/](https://agmarknet.gov.in/)
- **Authority**: Directorate of Marketing & Inspection (DMI), Ministry of Agriculture & Farmers Welfare.
- **Coverage**: Over 3,200 regulated wholesale markets across 35 States and UTs.
- **Formats Available**: HTML reports, scheduled CSV export, SOAP/XML web services for institutional partners.
- **Strengths**: Highest official authority and direct source for statutory minimum/modal prices.

---

### C. e-NAM (National Agriculture Market)
- **Portal URL**: [https://enam.gov.in/](https://enam.gov.in/)
- **Authority**: Small Farmers' Agribusiness Consortium (SFAC).
- **Coverage**: Electronic trading platform spanning 1,361 mandis across 23 States.
- **Key Differentiation**: Reports electronic auction bid prices, trade volumes, and quality assaying parameters (moisture, foreign matter, size grade).

---

## 3. Data Integration Challenges & Schema Normalization

When consuming raw mandi data feeds, our analytics and ingestion modules must account for several structural anomalies:

1. **Unit Discrepancies**:
   - Mandi prices are recorded in **INR per Quintal** (100 kg).
   - FarmCart lists produce in **INR per kg**.
   - *Normalization*: Price per kg = `modal_price / 100.0`.
2. **Commodity Nomenclature Drift**:
   - Different mandis record commodities with regional spellings (e.g., "Bhindi" vs "Ladies Finger" vs "Okra", "Batata" vs "Alu" vs "Potato").
   - *Normalization*: A canonical commodity alias table must be maintained in `analytics/mandi_analysis.py`.
3. **Missing Weekend / Holiday Data**:
   - Mandis are closed on Sundays and statutory holidays.
   - *Mitigation*: Forward-fill the last known modal price with a 3-day stale flag.
4. **Outlier & Reporting Errors**:
   - Clerical errors occasionally insert prices like 0 INR or 99,999 INR.
   - *Mitigation*: Filter out records where `min_price <= 0` or where `max_price > 5 * modal_price` using `analytics/data_quality.py`.

---

## 4. Phase 1 Implementation & Phase 2 Roadmap

- **Phase 1 (Current)**:
  - Database table `mandi_price_records` is created by Swyam Shukla.
  - Realistic benchmark datasets for key commodities (Potato, Onion, Tomato, Wheat, Rice) are seeded in `seed.py`.
  - Offline analysis and data validation scripts (`analytics/mandi_analysis.py`, `analytics/data_quality.py`) are provided by Mansi Jain.
  - Interactive dashboard (`frontend/analytics.html`) visualizes trends.
- **Phase 2 (Roadmap)**:
  - Background asynchronous cron worker using `httpx` to poll `data.gov.in` API daily at 21:00 IST.
  - Automated SMS/Push price advisory alerting farmers when their listed price is >20% below current terminal market modal prices.
