// ============================================================
// FarmCart Market Analytics Controller
// Primary Maintainer: Mansi Jain (Data Analyst & Testing Engineer)
// ============================================================

// Client-side benchmark dataset (aligned with Agmarknet / data.gov.in standards)
const BENCHMARK_DATA = {
  Tomato: {
    mandi: "Azadpur Mandi (Delhi)",
    series: [
      { date: "26 Oct", modal: 2200 },
      { date: "27 Oct", modal: 2300 },
      { date: "28 Oct", modal: 2400 },
      { date: "29 Oct", modal: 2500 },
      { date: "30 Oct", modal: 2650 },
      { date: "31 Oct", modal: 2750 },
      { date: "01 Nov", modal: 2850 },
    ],
    minPrice: 1800,
    maxPrice: 3300,
  },
  Onion: {
    mandi: "Lasalgaon Mandi (Maharashtra)",
    series: [
      { date: "26 Oct", modal: 2050 },
      { date: "27 Oct", modal: 2100 },
      { date: "28 Oct", modal: 2150 },
      { date: "29 Oct", modal: 2150 },
      { date: "30 Oct", modal: 2200 },
      { date: "31 Oct", modal: 2250 },
      { date: "01 Nov", modal: 2300 },
    ],
    minPrice: 1600,
    maxPrice: 2700,
  },
  Potato: {
    mandi: "Agra Mandi (Uttar Pradesh)",
    series: [
      { date: "26 Oct", modal: 1400 },
      { date: "27 Oct", modal: 1420 },
      { date: "28 Oct", modal: 1450 },
      { date: "29 Oct", modal: 1480 },
      { date: "30 Oct", modal: 1500 },
      { date: "31 Oct", modal: 1520 },
      { date: "01 Nov", modal: 1550 },
    ],
    minPrice: 1200,
    maxPrice: 1750,
  },
};

let currentCommodity = "Tomato";

document.addEventListener("DOMContentLoaded", () => {
  initAnalytics();
});

function initAnalytics() {
  const tabs = document.querySelectorAll("#commodity-tabs .tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      currentCommodity = tab.dataset.comm;
      renderCommodityView(currentCommodity);
    });
  });

  renderCommodityView(currentCommodity);
}

function renderCommodityView(commName) {
  const data = BENCHMARK_DATA[commName];
  if (!data) return;

  const series = data.series;
  const latest = series[series.length - 1].modal;
  const latestKg = (latest / 100).toFixed(2);

  // 7-day average
  const sum = series.reduce((acc, curr) => acc + curr.modal, 0);
  const ma7 = (sum / series.length / 100).toFixed(2);

  // Spread
  const spread = ((data.maxPrice - data.minPrice) / 100).toFixed(2);
  const spreadPct = (((data.maxPrice - data.minPrice) / (latest || 1)) * 100).toFixed(1);

  // Farmer Realization Gain (8% FarmCart fee vs 12% traditional mandi deductions)
  const mandiNet = (latestKg * 0.88).toFixed(2);
  const farmcartNet = (latestKg * 0.92).toFixed(2);
  const surplus = (farmcartNet - mandiNet).toFixed(2);
  const gainPct = (((farmcartNet - mandiNet) / mandiNet) * 100).toFixed(2);

  // Update DOM metrics
  document.getElementById("stat-modal-price").textContent = `₹${latestKg}/kg`;
  document.getElementById("stat-modal-quintal").textContent = `₹${latest.toLocaleString()} / quintal`;

  document.getElementById("stat-ma7-price").textContent = `₹${ma7}/kg`;
  document.getElementById("stat-ma7-trend").textContent =
    latestKg >= ma7 ? "Trending Upward ↑" : "Trending Downward ↓";

  document.getElementById("stat-spread").textContent = `₹${spread}/kg`;
  document.getElementById("stat-spread-pct").textContent = `${spreadPct}% Weekly Spread`;

  document.getElementById("stat-farmer-gain").textContent = `+₹${surplus}/kg`;

  renderSvgChart(series);
}

function renderSvgChart(series) {
  const container = document.getElementById("chart-container");
  if (!container) return;

  const width = container.clientWidth || 700;
  const height = 240;
  const padding = { top: 20, right: 30, bottom: 40, left: 50 };

  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const prices = series.map((s) => s.modal);
  const minPrice = Math.min(...prices) * 0.95;
  const maxPrice = Math.max(...prices) * 1.05;

  const getX = (index) => padding.left + (index / (series.length - 1)) * chartW;
  const getY = (val) => padding.top + chartH - ((val - minPrice) / (maxPrice - minPrice)) * chartH;

  // Build SVG Points
  const points = series.map((s, idx) => `${getX(idx)},${getY(s.modal)}`).join(" ");

  // Generate Y-axis gridlines
  let yAxisSvg = "";
  const yTicks = 4;
  for (let i = 0; i <= yTicks; i++) {
    const val = minPrice + (i / yTicks) * (maxPrice - minPrice);
    const y = getY(val);
    yAxisSvg += `
      <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" stroke="#dfe9e2" stroke-dasharray="4" />
      <text x="${padding.left - 8}" y="${y + 4}" font-size="10" fill="#6b7c71" text-anchor="end" font-family="'JetBrains Mono', monospace">₹${Math.round(val)}</text>
    `;
  }

  // Generate X-axis labels and points
  let xLabelsSvg = "";
  let dotsSvg = "";
  series.forEach((s, idx) => {
    const x = getX(idx);
    const y = getY(s.modal);
    xLabelsSvg += `
      <text x="${x}" y="${height - 12}" font-size="11" fill="#6b7c71" text-anchor="middle" font-family="'DM Sans', sans-serif">${s.date}</text>
    `;
    dotsSvg += `
      <circle cx="${x}" cy="${y}" r="5" fill="#1d6f42" stroke="#ffffff" stroke-width="2" />
      <text x="${x}" y="${y - 10}" font-size="11" font-weight="700" fill="#173322" text-anchor="middle" font-family="'JetBrains Mono', monospace">₹${s.modal}</text>
    `;
  });

  const svgContent = `
    <svg width="100%" height="100%" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      ${yAxisSvg}
      <polyline fill="none" stroke="#1d6f42" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="${points}" />
      ${dotsSvg}
      ${xLabelsSvg}
    </svg>
  `;

  container.innerHTML = svgContent;
}
