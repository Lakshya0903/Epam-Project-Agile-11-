// ============================================================
// FarmCart Market Price Intelligence & Analytics Controller
// Phase 3: Dynamic District/Mandi Cascades, 90-Day Analytics,
// Deterministic Selling-Price Guidance & Admin CSV Ingestion
// ============================================================

let currentCommodity = "Tomato";
let currentState = "";
let currentDistrict = "";
let currentMandi = "";
let activeAnalyticsRequestId = 0;

document.addEventListener("DOMContentLoaded", () => {
  initAnalytics();
});

async function initAnalytics() {
  setupUserRoleUI();
  setupCommodityTabs();
  setupFilterListeners();
  setupAdminImportForm();
  await loadDistricts();
}

// ------------------------------------------------------------
// 1. Role UI Verification
// ------------------------------------------------------------
function setupUserRoleUI() {
  const user = Auth.getUser();
  if (user) {
    const roleBadge = document.getElementById("nav-user-role");
    if (roleBadge) {
      roleBadge.textContent = `${user.role.toUpperCase()} • ${user.name || ""}`.trim();
    }
    if (user.role === "admin") {
      const adminPanel = document.getElementById("admin-import-panel");
      if (adminPanel) adminPanel.style.display = "block";
    }
  }
}

// ------------------------------------------------------------
// 2. Commodity Tabs Setup
// ------------------------------------------------------------
function setupCommodityTabs() {
  const tabs = document.querySelectorAll("#commodity-tabs .tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      currentCommodity = tab.dataset.comm;
      loadAnalyticsData();
    });
  });
}

// ------------------------------------------------------------
// 3. District & Mandi Filter Listeners
// ------------------------------------------------------------
function setupFilterListeners() {
  const distSelect = document.getElementById("sel-district");
  const mandiSelect = document.getElementById("sel-mandi");

  if (distSelect) {
    distSelect.addEventListener("change", async () => {
      currentDistrict = distSelect.value;
      currentMandi = "";
      await loadMandisForDistrict(currentDistrict);
      loadAnalyticsData();
    });
  }

  if (mandiSelect) {
    mandiSelect.addEventListener("change", () => {
      currentMandi = mandiSelect.value;
      loadAnalyticsData();
    });
  }
}

async function loadDistricts() {
  const distSelect = document.getElementById("sel-district");
  if (!distSelect) return;

  try {
    const districts = await apiRequest("/analytics/locations/districts", { auth: false });
    distSelect.innerHTML = "";

    if (!districts || districts.length === 0) {
      distSelect.innerHTML = `<option value="">All Districts (National)</option>`;
      currentDistrict = "";
    } else {
      distSelect.innerHTML = `<option value="">All Districts (National)</option>`;
      districts.forEach((d) => {
        const opt = document.createElement("option");
        opt.value = d;
        opt.textContent = d;
        distSelect.appendChild(opt);
      });
      // Default to first available district
      if (districts.length > 0) {
        distSelect.value = districts[0];
        currentDistrict = districts[0];
      }
    }

    await loadMandisForDistrict(currentDistrict);
    loadAnalyticsData();
  } catch (err) {
    console.warn("Could not load districts from API:", err);
    distSelect.innerHTML = `<option value="">All Districts</option>`;
    loadAnalyticsData();
  }
}

async function loadMandisForDistrict(district) {
  const mandiSelect = document.getElementById("sel-mandi");
  if (!mandiSelect) return;

  try {
    const path = district ? `/analytics/locations/mandis?district=${encodeURIComponent(district)}` : "/analytics/locations/mandis";
    const mandis = await apiRequest(path, { auth: false });
    mandiSelect.innerHTML = `<option value="">All Mandis in District</option>`;

    if (mandis && mandis.length > 0) {
      mandis.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = `${m} Mandi`;
        mandiSelect.appendChild(opt);
      });
    }
  } catch (err) {
    console.warn("Could not load mandis:", err);
    mandiSelect.innerHTML = `<option value="">All Mandis</option>`;
  }
}

// ------------------------------------------------------------
// 4. Load Market Summary & Price Guidance (Race-Condition Free)
// ------------------------------------------------------------
async function loadAnalyticsData() {
  const reqId = ++activeAnalyticsRequestId;

  const scopeText = `${currentState ? currentState + " • " : ""}${currentDistrict || "All Districts"} ${currentMandi ? "• " + currentMandi + " Mandi" : ""}`.trim();
  const metaScope = document.getElementById("meta-scope");
  if (metaScope) metaScope.textContent = scopeText;

  // Build query params
  const params = new URLSearchParams();
  params.append("commodity", currentCommodity);
  if (currentState) params.append("state", currentState);
  if (currentDistrict) params.append("district", currentDistrict);
  if (currentMandi) params.append("market", currentMandi);

  // Show loading indicator in stat boxes if desired
  const chartBox = document.getElementById("chart-container");

  try {
    // Parallel fetch: Summary analytics and Selling-price guidance
    const [summary, guidance] = await Promise.all([
      apiRequest(`/analytics/summary?${params.toString()}`, { auth: false }).catch(() => null),
      apiRequest(`/analytics/selling-price-guidance?${params.toString()}`, { auth: false }).catch(() => null),
    ]);

    // Discard response if a newer selection request has been initiated
    if (reqId !== activeAnalyticsRequestId) {
      console.debug("Discarding out-of-order analytics response for id", reqId);
      return;
    }

    renderSummaryMetrics(summary);
    renderPriceGuidance(guidance);
  } catch (err) {
    if (reqId === activeAnalyticsRequestId) {
      console.error("Error loading analytics data:", err);
      renderSummaryMetrics(null);
      renderPriceGuidance(null);
    }
  }
}

function renderSummaryMetrics(summary) {
  if (!summary) {
    // Empty state
    document.getElementById("stat-modal-price").textContent = "₹--/kg";
    document.getElementById("stat-modal-quintal").textContent = "No data recorded";
    document.getElementById("stat-ma7-price").textContent = "₹--/kg";
    document.getElementById("stat-ma7-trend").textContent = "Insufficient data";
    document.getElementById("stat-spread").textContent = "₹--/kg";
    document.getElementById("stat-spread-pct").textContent = "--";
    document.getElementById("stat-movement").textContent = "--%";
    document.getElementById("stat-movement-label").textContent = "No records";

    const metaSourceBadge = document.getElementById("meta-source-badge");
    if (metaSourceBadge) metaSourceBadge.textContent = "Source: No Data";
    const metaCacheBadge = document.getElementById("meta-cache-badge");
    if (metaCacheBadge) {
      metaCacheBadge.className = "badge";
      metaCacheBadge.textContent = "Cache: None";
    }

    const chartBox = document.getElementById("chart-container");
    if (chartBox) {
      chartBox.innerHTML = `
        <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; height:100%; color:var(--paper-dim);">
          <span style="font-size:2rem; margin-bottom:8px;">🌾</span>
          <span>No historical mandi observations found within the 90-day window.</span>
          <span style="font-size:0.85rem; margin-top:4px;">Try selecting a different district, or administrators may import official CSV benchmark records below.</span>
        </div>`;
    }
    return;
  }

  // Provenance bar
  const metaDate = document.getElementById("meta-date");
  if (metaDate) metaDate.textContent = summary.latest_arrival_date || "--";

  const metaFetchTime = document.getElementById("meta-fetch-time");
  if (metaFetchTime) {
    metaFetchTime.textContent = summary.last_successful_fetch_at || summary.last_fetched_at
      ? new Date(summary.last_successful_fetch_at || summary.last_fetched_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : "Cached";
  }

  const metaSourceBadge = document.getElementById("meta-source-badge");
  if (metaSourceBadge) {
    if (summary.data_source === "ogd_api") {
      metaSourceBadge.textContent = "Source: Official OGD India API";
    } else if (summary.data_source === "csv_import") {
      metaSourceBadge.textContent = "Source: Official Mandi CSV Import";
    } else {
      metaSourceBadge.textContent = "Source: Demonstration / Seed Data";
    }
  }

  const metaCacheBadge = document.getElementById("meta-cache-badge");
  if (metaCacheBadge) {
    if (summary.is_stale) {
      metaCacheBadge.className = "badge warning";
      metaCacheBadge.textContent = "Cache: Stale (Fallback)";
    } else {
      metaCacheBadge.className = "badge success";
      metaCacheBadge.textContent = "Cache: Fresh";
    }
  }

  // 1. Latest Modal Price
  document.getElementById("stat-modal-price").textContent = `₹${summary.latest_modal_kg.toFixed(2)}/kg`;
  document.getElementById("stat-modal-quintal").textContent = `₹${summary.latest_modal_quintal.toLocaleString()} / quintal`;

  // 2. 7-Day Moving Avg
  document.getElementById("stat-ma7-price").textContent = `₹${summary.moving_average_kg.toFixed(2)}/kg`;
  const trendEl = document.getElementById("stat-ma7-trend");
  if (trendEl) {
    if (summary.trend_direction === "upward") {
      trendEl.className = "trend up";
      trendEl.textContent = "Trending Upward ↑";
    } else if (summary.trend_direction === "downward") {
      trendEl.className = "trend down";
      trendEl.textContent = "Trending Downward ↓";
    } else {
      trendEl.className = "trend";
      trendEl.textContent = "Stable Trend →";
    }
  }

  // 3. Price Spread & Extrema
  document.getElementById("stat-spread").textContent = `₹${summary.historical_min_kg.toFixed(2)} – ₹${summary.historical_max_kg.toFixed(2)}/kg`;
  document.getElementById("stat-spread-pct").textContent = `Spread: ₹${(summary.historical_max_kg - summary.historical_min_kg).toFixed(2)}/kg (${summary.sample_days} days)`;

  // 4. Price Movement
  const moveEl = document.getElementById("stat-movement");
  if (moveEl) {
    const sign = summary.price_change_pct > 0 ? "+" : "";
    moveEl.textContent = `${sign}${summary.price_change_pct.toFixed(1)}%`;
    moveEl.style.color = summary.price_change_pct >= 0 ? "var(--wheat)" : "var(--danger)";
  }
  document.getElementById("stat-movement-label").textContent = `${summary.trend_direction.toUpperCase()} (${summary.date_range_start || ""} to ${summary.date_range_end || ""})`;

  // Render SVG Line Chart
  renderPriceChart(summary.daily_series || []);
}

function renderPriceGuidance(guidance) {
  const container = document.getElementById("guidance-container");
  const rangeVal = document.getElementById("guidance-range-val");
  const subtext = document.getElementById("guidance-subtext");
  const sampleBadge = document.getElementById("guidance-sample-badge");

  if (!container || !rangeVal) return;

  if (!guidance || !guidance.is_sufficient) {
    rangeVal.textContent = "Price Guidance Unavailable";
    rangeVal.style.fontSize = "1.5rem";
    rangeVal.style.color = "var(--paper-dim)";
    if (subtext) {
      subtext.textContent = guidance?.reason_if_insufficient || "Insufficient historical data recorded for this area.";
    }
    if (sampleBadge) sampleBadge.textContent = "Limited Data";
    return;
  }

  rangeVal.style.fontSize = "2.2rem";
  rangeVal.style.color = "var(--wheat)";
  rangeVal.textContent = `₹${guidance.suggested_min_price_kg.toFixed(2)} – ₹${guidance.suggested_max_price_kg.toFixed(2)} / kg`;

  if (sampleBadge) {
    sampleBadge.textContent = `${guidance.sample_observations} observations (${guidance.date_window_days}-day window)`;
  }

  if (subtext) {
    subtext.innerHTML = `
      Recommended market range based on the <strong>25th percentile (Q1: ₹${guidance.suggested_min_price_kg}/kg)</strong> 
      and <strong>75th percentile (Q3: ₹${guidance.suggested_max_price_kg}/kg)</strong> of official wholesale modal prices.
    `;
  }
}

// ------------------------------------------------------------
// 5. SVG Historical Price Trajectory Chart
// ------------------------------------------------------------
function renderPriceChart(series) {
  const chartBox = document.getElementById("chart-container");
  const tooltip = document.getElementById("chart-tooltip");
  if (!chartBox) return;

  if (!series || series.length === 0) {
    chartBox.innerHTML = `
      <div style="display:flex; justify-content:center; align-items:center; height:100%; color:var(--paper-dim);">
        No daily observations available to plot.
      </div>`;
    return;
  }

  const W = 800;
  const H = 240;
  const padL = 60;
  const padR = 30;
  const padT = 30;
  const padB = 40;

  const innerW = W - padL - padR;
  const innerH = H - padT - padB;

  const prices = series.map((s) => s.modal_price_kg);
  let minP = Math.min(...prices);
  let maxP = Math.max(...prices);

  // Buffer range
  if (minP === maxP) {
    minP = Math.max(0, minP - 5);
    maxP = maxP + 5;
  } else {
    const diff = maxP - minP;
    minP = Math.max(0, minP - diff * 0.15);
    maxP = maxP + diff * 0.15;
  }

  const n = series.length;
  const getX = (i) => padL + (n === 1 ? innerW / 2 : (i / (n - 1)) * innerW);
  const getY = (val) => padT + innerH - ((val - minP) / (maxP - minP)) * innerH;

  // Build points & path
  let pathD = "";
  const points = [];

  series.forEach((pt, i) => {
    const x = getX(i);
    const y = getY(pt.modal_price_kg);
    points.push({ x, y, pt });
    if (i === 0) {
      pathD += `M ${x.toFixed(1)} ${y.toFixed(1)}`;
    } else {
      pathD += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
    }
  });

  // SVG Markup
  let svg = `
    <svg viewBox="0 0 ${W} ${H}" style="width:100%; height:100%; display:block;" preserveAspectRatio="none">
      <!-- Grid Lines -->
      <line x1="${padL}" y1="${padT}" x2="${W - padR}" y2="${padT}" stroke="var(--line)" stroke-dasharray="4 4" />
      <line x1="${padL}" y1="${padT + innerH / 2}" x2="${W - padR}" y2="${padT + innerH / 2}" stroke="var(--line)" stroke-dasharray="4 4" />
      <line x1="${padL}" y1="${padT + innerH}" x2="${W - padR}" y2="${padT + innerH}" stroke="var(--line)" />

      <!-- Y-Axis Price Labels -->
      <text x="${padL - 10}" y="${padT + 4}" font-size="11" fill="var(--paper-dim)" text-anchor="end">₹${maxP.toFixed(1)}</text>
      <text x="${padL - 10}" y="${padT + innerH / 2 + 4}" font-size="11" fill="var(--paper-dim)" text-anchor="end">₹${((maxP + minP) / 2).toFixed(1)}</text>
      <text x="${padL - 10}" y="${padT + innerH + 4}" font-size="11" fill="var(--paper-dim)" text-anchor="end">₹${minP.toFixed(1)}</text>

      <!-- Gradient Area -->
      <defs>
        <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--wheat)" stop-opacity="0.28" />
          <stop offset="100%" stop-color="var(--wheat)" stop-opacity="0.0" />
        </linearGradient>
      </defs>
      <path d="${pathD} L ${points[points.length - 1].x} ${padT + innerH} L ${points[0].x} ${padT + innerH} Z" fill="url(#chartGrad)" />

      <!-- Main Trend Line -->
      <path d="${pathD}" fill="none" stroke="var(--wheat)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />

      <!-- Data Dots -->
  `;

  points.forEach((p, idx) => {
    // Show dates on x-axis (skip every other if dense)
    const showLabel = n <= 8 || idx % Math.ceil(n / 6) === 0 || idx === n - 1;
    if (showLabel) {
      const displayDate = p.pt.date.length > 5 ? p.pt.date.slice(5) : p.pt.date;
      svg += `<text x="${p.x}" y="${padT + innerH + 20}" font-size="11" fill="var(--paper-dim)" text-anchor="middle">${displayDate}</text>`;
    }

    svg += `
      <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="5" fill="#fff" stroke="var(--wheat)" stroke-width="2.5" class="chart-point" data-idx="${idx}" style="cursor:pointer;" />
    `;
  });

  svg += `</svg>`;
  chartBox.innerHTML = svg;

  // Tooltip interaction
  const circles = chartBox.querySelectorAll(".chart-point");
  circles.forEach((circle) => {
    circle.addEventListener("mouseenter", (e) => {
      const idx = e.target.dataset.idx;
      const data = series[idx];
      if (!data || !tooltip) return;

      circle.setAttribute("r", "7");
      circle.setAttribute("fill", "var(--clay)");

      tooltip.innerHTML = `
        <strong>${data.date}</strong><br/>
        Modal: <strong>₹${data.modal_price_kg.toFixed(2)}/kg</strong> (₹${data.modal_price_quintal}/q)<br/>
        Range: ₹${(data.min_price_quintal / 100).toFixed(2)} – ₹${(data.max_price_quintal / 100).toFixed(2)}/kg
      `;
      tooltip.style.display = "block";
      const rect = chartBox.getBoundingClientRect();
      tooltip.style.left = `${e.clientX - rect.left + 12}px`;
      tooltip.style.top = `${e.clientY - rect.top - 20}px`;
    });

    circle.addEventListener("mouseleave", () => {
      circle.setAttribute("r", "5");
      circle.setAttribute("fill", "#fff");
      if (tooltip) tooltip.style.display = "none";
    });
  });
}

// ------------------------------------------------------------
// 6. Admin Official CSV Upload Handler
// ------------------------------------------------------------
function setupAdminImportForm() {
  const form = document.getElementById("csv-import-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById("csv-file-input");
    const msgEl = document.getElementById("csv-upload-msg");
    const auditReport = document.getElementById("csv-audit-report");
    const btn = document.getElementById("btn-upload-csv");

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      if (msgEl) msgEl.innerHTML = `<div class="error-box">Please select a valid official .csv file.</div>`;
      return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    try {
      btn.disabled = true;
      btn.textContent = "Processing ingestion...";
      if (msgEl) msgEl.innerHTML = `<div class="small-note">Uploading and validating CSV dataset...</div>`;

      const result = await apiRequest("/analytics/mandi-prices/import", {
        method: "POST",
        body: formData,
      });

      if (msgEl) {
        msgEl.innerHTML = `<div class="success-box">CSV processed successfully! ${result.inserted} inserted, ${result.updated} updated, ${result.skipped} duplicates skipped.</div>`;
      }

      if (auditReport) {
        auditReport.style.display = "block";
        document.getElementById("audit-total").textContent = result.total_rows;
        document.getElementById("audit-inserted").textContent = result.inserted;
        document.getElementById("audit-updated").textContent = result.updated;
        document.getElementById("audit-rejected").textContent = result.rejected;

        const errList = document.getElementById("audit-errors-list");
        if (errList) {
          if (result.errors && result.errors.length > 0) {
            errList.innerHTML = `<strong>Validation anomalies:</strong><ul>` + result.errors.map((err) => `<li>${err}</li>`).join("") + `</ul>`;
          } else {
            errList.innerHTML = `<span style="color:var(--wheat);">✓ Zero validation errors encountered.</span>`;
          }
        }
      }

      form.reset();
      // Reload geographic options and active view
      await loadDistricts();
    } catch (err) {
      if (msgEl) msgEl.innerHTML = `<div class="error-box">${err.message}</div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = "Upload & Process Ingestion";
    }
  });
}
