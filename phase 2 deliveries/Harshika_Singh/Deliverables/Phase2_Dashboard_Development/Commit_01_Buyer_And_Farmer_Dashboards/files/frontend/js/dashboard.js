Auth.requireLogin();
const user = Auth.getUser();

document.getElementById("role-badge").textContent = user.role;
document.getElementById("user-name").textContent = user.name;

// ============================================================
// CANONICAL 5-STATE ORDER LIFECYCLE & RAIL
// ============================================================

const STATIONS = ["Placed", "Confirmed", "Processing", "Shipped", "Delivered"];
const STATUS_INDEX = {
  placed: 0,
  confirmed: 1, matched: 1,
  processing: 2, batched: 2,
  shipped: 3, out_for_delivery: 3,
  delivered: 4, paid: 4, settled: 4,
  cancelled: -1
};

function renderRail(status) {
  const normStatus = (status || "").toLowerCase();
  if (normStatus === "cancelled") {
    return `
      <div style="background:#fee2e2; color:#991b1b; padding:8px 14px; border-radius:8px; font-weight:600; font-size:0.85rem; margin:10px 0;">
        ⛔ Order Cancelled
      </div>
    `;
  }

  const idx = STATUS_INDEX[normStatus] ?? 0;
  const pct = idx <= 0 ? 0 : (idx / (STATIONS.length - 1)) * 100;
  const stations = STATIONS.map((label, i) => {
    const cls = i < idx ? "done" : (i === idx ? "current" : "");
    return `<div class="station ${cls}"><div class="dot">${i < idx ? "✓" : i + 1}</div><div class="label">${label}</div></div>`;
  }).join("");

  return `
    <div class="rail" style="--stations:${STATIONS.length}">
      <div class="rail-fill" style="width:${pct}%"></div>
      ${stations}
    </div>
  `;
}


// ============================================================
// FARMER SECTION
// ============================================================

async function initFarmer() {
  document.getElementById("farmer-view").style.display = "block";

  document.getElementById("produce-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = document.getElementById("produce-msg");
    msg.innerHTML = "";
    try {
      await apiRequest("/produce", {
        method: "POST",
        body: {
          product_name: document.getElementById("p-name").value,
          quantity_available: parseFloat(document.getElementById("p-qty").value),
          unit: document.getElementById("p-unit").value,
          quality_grade: document.getElementById("p-grade").value,
          price_per_unit: parseFloat(document.getElementById("p-price").value),
          available_date: document.getElementById("p-date").value ? new Date(document.getElementById("p-date").value).toISOString() : null,
          pickup_location: document.getElementById("p-location").value,
        },
      });
      msg.innerHTML = `<div class="success-box">Listed on the platform.</div>`;
      document.getElementById("produce-form").reset();
      loadMyProduce();
    } catch(err) {
      msg.innerHTML = `<div class="error-box">${err.message}</div>`;
    }
  });

  loadMyProduce();
  loadFarmerOrders();
}

async function loadMyProduce() {
  const list = document.getElementById("my-produce-list");
  list.innerHTML = `<p class="small-note">Loading listed produce...</p>`;
  try {
    const items = await apiRequest("/produce/mine");
    if (!items.length) {
      list.innerHTML = `<p class="small-note">You haven't listed any produce yet.</p>`;
      return;
    }
    list.innerHTML = items.map(p => `
      <div class="produce-card">
        <div class="name">${p.product_name}</div>
        <div class="meta">${p.quantity_available} ${p.unit} available · Grade ${p.quality_grade}</div>
        <div class="meta">Pickup: ${p.pickup_location}</div>
        <div class="price-tag">₹${p.price_per_unit} / ${p.unit}</div>
        <span class="badge">${p.status}</span>
      </div>
    `).join("");
  } catch(err) {
    list.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}

async function loadFarmerOrders() {
  const list = document.getElementById("farmer-orders-list");
  if (!list) return;
  list.innerHTML = `<p class="small-note">Loading incoming orders...</p>`;
  try {
    const orders = await apiRequest("/orders/farmer");
    if (!orders || !orders.length) {
      list.innerHTML = `<p class="small-note">No incoming orders yet. Orders will appear here as buyers purchase your produce.</p>`;
      return;
    }

    list.innerHTML = orders.map(o => {
      const normStatus = (o.status || "").toLowerCase();
      let actionBtn = "";
      if (normStatus === "placed") {
        actionBtn = `
          <button class="btn small" style="margin-top:10px;" onclick="advanceOrderStatus('${o.id}', 'confirmed')">
            Confirm Order
          </button>
        `;
      } else if (normStatus === "confirmed") {
        actionBtn = `
          <button class="btn small secondary" style="margin-top:10px;" onclick="advanceOrderStatus('${o.id}', 'processing')">
            Mark Packed & Processing
          </button>
        `;
      } else if (normStatus === "processing") {
        actionBtn = `
          <span class="badge" style="background:#eaf7ef; color:#1d6f42; margin-top:10px; display:inline-block;">
            Ready for Logistics Pickup
          </span>
        `;
      }

      return `
        <div class="card" style="margin-bottom:12px;">
          <div class="order-row-head">
            <div><strong>Order #${o.id.slice(0,8)}</strong> · Type: ${o.order_type}</div>
            <span class="badge">${o.status}</span>
          </div>
          <div class="small-note" style="margin-top:4px;">
            Deliver to: ${o.delivery_location} ${o.delivery_pincode ? `(PIN: ${o.delivery_pincode})` : ""} · Slot: ${o.delivery_slot}
          </div>
          <div style="margin-top:8px;">
            ${renderRail(o.status)}
          </div>
          <table style="margin-top:10px;">
            <thead><tr><th>Product ID</th><th>Quantity</th><th>Unit Price</th><th>Subtotal</th></tr></thead>
            <tbody>
              ${o.items.map(i => `<tr><td>${i.produce_id.slice(0,8)}</td><td>${i.quantity}</td><td>₹${i.unit_price}</td><td>₹${i.subtotal.toFixed(2)}</td></tr>`).join("")}
            </tbody>
          </table>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px;">
            <strong>Order Total: ₹${Number(o.total_amount).toFixed(2)}</strong>
            <div>${actionBtn}</div>
          </div>
        </div>
      `;
    }).join("");
  } catch(err) {
    list.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}

async function advanceOrderStatus(orderId, nextStatus) {
  try {
    await apiRequest(`/orders/${orderId}/status`, {
      method: "POST",
      body: { status: nextStatus, notes: `Status updated by farmer to ${nextStatus}` }
    });
    alert(`Order #${orderId.slice(0,8)} marked as ${nextStatus.toUpperCase()}!`);
    loadFarmerOrders();
  } catch(err) {
    alert(`Error updating order: ${err.message}`);
  }
}


// ============================================================
// BUYER SECTION
// ============================================================

const CART_KEY = `farmcart_cart_${user.id}`;
function getCart() { 
  const saved = localStorage.getItem(CART_KEY) || localStorage.getItem(`f2m_cart_${user.id}`) || "[]";
  return JSON.parse(saved); 
}
function setCart(cart) { 
  localStorage.setItem(CART_KEY, JSON.stringify(cart)); 
  localStorage.setItem(`f2m_cart_${user.id}`, JSON.stringify(cart)); 
  updateCartCount(); 
}
function updateCartCount() {
  const count = getCart().reduce((n, i) => n + 1, 0);
  const el = document.getElementById("cart-count");
  if (el) el.textContent = count ? `(${count})` : "";
}

async function initBuyer() {
  document.getElementById("buyer-view").style.display = "block";
  document.getElementById("buyer-type-label").textContent =
    user.buyer_type === "bulk" ? "Bulk buyer" : "Individual buyer";

  document.querySelectorAll("[data-btab]").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll("[data-btab]").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      ["market", "cart", "orders"].forEach(name => {
        document.getElementById(`btab-${name}`).style.display = (name === tab.dataset.btab) ? "block" : "none";
      });
      if (tab.dataset.btab === "cart") renderCart();
      if (tab.dataset.btab === "orders") loadOrders();
    });
  });

  const searchBox = document.getElementById("search-box");
  if (searchBox) {
    searchBox.addEventListener("input", (e) => loadMarketplace(e.target.value));
  }
  
  const placeOrderBtn = document.getElementById("place-order-btn");
  if (placeOrderBtn) {
    placeOrderBtn.addEventListener("click", placeOrder);
  }

  updateCartCount();
  loadMarketplace();
}

async function loadMarketplace(search = "") {
  const list = document.getElementById("marketplace-list");
  list.innerHTML = `<p class="small-note">Loading marketplace...</p>`;
  try {
    const qs = search ? `?product_name=${encodeURIComponent(search)}` : "";
    const items = await apiRequest(`/produce${qs}`);
    if (!items.length) {
      list.innerHTML = `<p class="small-note">No produce currently available.</p>`;
      return;
    }
    list.innerHTML = items.map(p => `
      <div class="produce-card">
        <div class="name">${p.product_name}</div>
        <div class="meta">${p.quantity_available} ${p.unit} available · Grade ${p.quality_grade}</div>
        <div class="meta">Pickup: ${p.pickup_location}</div>
        <div class="price-tag">₹${p.price_per_unit} / ${p.unit}</div>
        <div class="qty-control">
          <input type="number" min="0.5" step="0.5" value="1" id="qty-${p.id}">
          <button class="btn small" onclick="addToCart('${p.id}', '${p.product_name.replace(/'/g, "\\'")}', ${p.price_per_unit}, '${p.unit}')">Add to cart</button>
        </div>
      </div>
    `).join("");
  } catch(err) {
    list.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}

function addToCart(produce_id, name, unit_price, unit) {
  const qtyInput = document.getElementById(`qty-${produce_id}`);
  const quantity = parseFloat(qtyInput.value) || 1;
  const cart = getCart();
  const existing = cart.find(i => i.produce_id === produce_id);
  if (existing) {
    existing.quantity += quantity;
  } else {
    cart.push({ produce_id, name, unit_price, unit, quantity });
  }
  setCart(cart);
  alert(`Added ${quantity} ${unit} of ${name} to cart.`);
}

function renderCart() {
  const cart = getCart();
  const body = document.getElementById("cart-body");
  if (!cart.length) {
    body.innerHTML = `<tr><td colspan="5" class="small-note">Your cart is empty.</td></tr>`;
  } else {
    body.innerHTML = cart.map((i, idx) => `
      <tr>
        <td>${i.name}</td>
        <td>${i.quantity} ${i.unit}</td>
        <td>₹${i.unit_price}</td>
        <td>₹${(i.quantity * i.unit_price).toFixed(2)}</td>
        <td><button class="btn-link" onclick="removeFromCart(${idx})">Remove</button></td>
      </tr>
    `).join("");
  }
  const total = cart.reduce((sum, i) => sum + i.quantity * i.unit_price, 0);
  document.getElementById("cart-total").textContent = `Total: ₹${total.toFixed(2)}`;
}

function removeFromCart(idx) {
  const cart = getCart();
  cart.splice(idx, 1);
  setCart(cart);
  renderCart();
}

// ---------------- PIN CODE & SERVICEABILITY ----------------
async function checkServiceability() {
  const pincode = (document.getElementById("delivery-pincode").value || "").trim();
  const statusDiv = document.getElementById("pin-serviceability-status");
  const dropPointSelect = document.getElementById("delivery-drop-point");
  statusDiv.innerHTML = "";

  if (!/^[1-9][0-9]{5}$/.test(pincode)) {
    statusDiv.innerHTML = `<div class="error-box">Please enter a valid 6-digit Indian PIN code (cannot start with 0).</div>`;
    return null;
  }

  statusDiv.innerHTML = `<p class="small-note">Checking nationwide delivery serviceability...</p>`;

  try {
    const res = await apiRequest(`/logistics/serviceability/${pincode}`);
    if (res.serviceable) {
      statusDiv.innerHTML = `
        <div class="success-box">
          <strong>Serviceable in ${res.zone_name} (${res.zone_code})</strong><br>
          Home Delivery: ${res.home_delivery_available ? "✓ Available" : "✗ Not available"}<br>
          Shared Drop Points: ${res.shared_drop_points_available ? `✓ (${res.drop_points.length} locations)` : "✗ None"}
        </div>
      `;

      // Populate drop points dropdown
      dropPointSelect.innerHTML = `<option value="">-- Choose a pickup hub --</option>`;
      if (res.drop_points && res.drop_points.length) {
        res.drop_points.forEach(dp => {
          const opt = document.createElement("option");
          opt.value = dp.id;
          opt.textContent = `${dp.name} — ${dp.physical_address} (${dp.operating_hours || "Open daily"})`;
          dropPointSelect.appendChild(opt);
        });
      }
      return res;
    } else {
      statusDiv.innerHTML = `<div class="error-box">${res.message || "PIN code is currently outside active delivery zones."}</div>`;
      return null;
    }
  } catch(err) {
    statusDiv.innerHTML = `<div class="error-box">${err.message}</div>`;
    return null;
  }
}

function onDeliveryModeChange() {
  const mode = document.getElementById("delivery-mode").value;
  const dropRow = document.getElementById("drop-point-selection-row");
  if (dropRow) {
    dropRow.style.display = (mode === "shared_drop_point") ? "block" : "none";
  }
}

async function placeOrder() {
  const msg = document.getElementById("order-msg");
  msg.innerHTML = "";
  const cart = getCart();
  const pincode = (document.getElementById("delivery-pincode").value || "").trim();
  const mode = document.getElementById("delivery-mode").value;
  const location = (document.getElementById("delivery-location").value || "").trim();
  const date = document.getElementById("delivery-date").value;
  const slot = document.getElementById("delivery-slot-time").value;
  const dropPointId = mode === "shared_drop_point" ? document.getElementById("delivery-drop-point").value : null;

  if (!cart.length) {
    msg.innerHTML = `<div class="error-box">Your cart is empty.</div>`;
    return;
  }
  if (!pincode || !/^[1-9][0-9]{5}$/.test(pincode)) {
    msg.innerHTML = `<div class="error-box">Please provide a valid 6-digit Indian PIN code.</div>`;
    return;
  }
  if (!location) {
    msg.innerHTML = `<div class="error-box">Please enter delivery address or landmark.</div>`;
    return;
  }
  if (!date) {
    msg.innerHTML = `<div class="error-box">Please choose a preferred delivery date.</div>`;
    return;
  }
  if (mode === "shared_drop_point" && !dropPointId) {
    msg.innerHTML = `<div class="error-box">Please select a shared drop point location.</div>`;
    return;
  }

  try {
    const order = await apiRequest("/orders", {
      method: "POST",
      body: {
        order_type: user.buyer_type === "bulk" ? "bulk" : "individual",
        delivery_location: location,
        delivery_pincode: pincode,
        delivery_mode: mode,
        shared_drop_point_id: dropPointId || null,
        delivery_slot: `${date}|${slot}`,
        items: cart.map(i => ({ produce_id: i.produce_id, quantity: i.quantity })),
      },
    });

    setCart([]);
    renderCart();
    msg.innerHTML = `<div class="success-box">Order placed successfully! Assigned to batch.</div>`;
    
    // Automatically switch to orders tab
    setTimeout(() => {
      const ordersTab = document.querySelector('[data-btab="orders"]');
      if (ordersTab) ordersTab.click();
    }, 1200);

  } catch(err) {
    msg.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}

// ---------------- ORDERS LIST & TRACKING ----------------
async function loadOrders() {
  const list = document.getElementById("orders-list");
  list.innerHTML = `<p class="small-note">Loading your orders...</p>`;
  try {
    const orders = await apiRequest("/orders/mine");
    if (!orders || !orders.length) {
      list.innerHTML = `<p class="small-note">No orders yet.</p>`;
      return;
    }

    list.innerHTML = "";
    for (const o of orders) {
      const row = document.createElement("div");
      row.className = "order-row";
      row.style.marginBottom = "24px";
      row.innerHTML = `
        <div class="order-row-head">
          <div><strong>Order #${o.id.slice(0,8)}</strong> · Mode: ${o.delivery_mode === "shared_drop_point" ? "Shared Drop Point" : "Home Delivery"}</div>
          <span class="badge">${o.status}</span>
        </div>
        <div class="small-note">Deliver to: ${o.delivery_location} ${o.delivery_pincode ? `(PIN: ${o.delivery_pincode})` : ""} · Slot: ${o.delivery_slot}</div>
        <div style="margin-top:8px;">${renderRail(o.status)}</div>
        <table style="margin-top:10px;">
          <thead><tr><th>Item ID</th><th>Quantity</th><th>Unit price</th><th>Subtotal</th></tr></thead>
          <tbody>
            ${o.items.map(i => `<tr><td>${i.produce_id.slice(0,8)}</td><td>${i.quantity}</td><td>₹${i.unit_price}</td><td>₹${i.subtotal.toFixed(2)}</td></tr>`).join("")}
          </tbody>
        </table>
        <div class="mono" style="margin-top:8px; font-weight:700;">Total: ₹${Number(o.total_amount).toFixed(2)}</div>
        <div id="extra-${o.id}" style="margin-top:14px;"></div>
      `;
      list.appendChild(row);
      loadOrderExtras(o);
    }
  } catch(err) {
    list.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}

async function loadOrderExtras(order) {
  const box = document.getElementById(`extra-${order.id}`);
  let html = "";

  const normStatus = (order.status || "").toLowerCase();

  // 1. Check order tracking details
  let tracking = null;
  try {
    tracking = await apiRequest(`/orders/${order.id}/tracking`);
  } catch(e) {
    // tracking endpoint fallback
  }

  // 2. Cancellation button for initial stages
  if (normStatus === "placed" || normStatus === "confirmed") {
    html += `
      <div style="margin-bottom:12px;">
        <button class="btn-link" style="color:var(--danger); font-size:0.85rem;" onclick="cancelBuyerOrder('${order.id}')">
          Cancel this order
        </button>
      </div>
    `;
  }

  // 3. Batching info
  if (normStatus === "processing" || normStatus === "batched" || normStatus === "matched") {
    html += `
      <div class="batch-window" style="margin-bottom:12px;">
        <strong>📦 Delivery Batch Allocation</strong>
        <div class="small-note" style="margin-top:4px;">
          Your order is securely grouped into an optimized delivery batch. Dual capacity validation (weight & order count) active.
        </div>
      </div>
    `;
  }

  // 4. Delivery record & Receiver confirmation without OTP
  let delivery = null;
  try {
    delivery = await apiRequest(`/orders/${order.id}/delivery`);
    if (delivery) {
      html += `
        <div class="small-note" style="margin-top:8px;">
          Logistics Partner: ${delivery.partner_name || "Assigned Fleet"} · Status: <strong>${delivery.status}</strong>
        </div>
      `;

      // Receiver confirmation button (authenticated receiver confirms receipt, no OTP)
      if (normStatus === "shipped" || normStatus === "delivered" || delivery.status === "shipped" || delivery.status === "delivered") {
        if (delivery.receiver_confirmed_at) {
          html += `
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; color:#166534; padding:8px 12px; border-radius:8px; margin-top:8px; font-size:0.88rem;">
              ✅ <strong>Receiver confirmation complete:</strong> You verified receipt on ${new Date(delivery.receiver_confirmed_at).toLocaleString()}.
            </div>
          `;
        } else {
          html += `
            <div style="background:#fffbeb; border:1px solid #fde68a; padding:10px 14px; border-radius:8px; margin-top:10px;">
              <strong>Delivery Received?</strong>
              <div class="small-note" style="margin-top:4px;">
                Confirm that your parcel has arrived safely. (Receiver confirmation does not require an OTP).
              </div>
              <button class="btn small" style="margin-top:8px;" onclick="confirmReceiverReceipt('${delivery.id}', '${order.id}')">
                Confirm Delivery Receipt
              </button>
            </div>
          `;
        }
      }
    }
  } catch(err) {
    // Delivery not created yet
  }

  // 5. 24-Hour Dispute Window
  if (normStatus === "delivered" || (delivery && delivery.status === "delivered")) {
    const isDisputeEligible = tracking ? tracking.dispute_eligible : true;
    const activeDispute = tracking ? tracking.active_dispute : null;

    if (activeDispute) {
      html += `
        <div style="background:#eff6ff; border:1px solid #bfdbfe; color:#1e40af; padding:12px; border-radius:8px; margin-top:12px;">
          <strong>⚠️ Active Dispute #${activeDispute.id.slice(0,8)}</strong>
          <div class="small-note" style="margin-top:4px;">
            Status: <strong>${activeDispute.status}</strong> · Reason: ${activeDispute.reason}<br>
            Description: "${activeDispute.description}"
          </div>
          ${activeDispute.resolution ? `
            <div style="margin-top:6px; font-weight:600;">
              Resolution: ${activeDispute.resolution} ${activeDispute.reviewer_notes ? `— "${activeDispute.reviewer_notes}"` : ""}
            </div>
          ` : `
            <div class="small-note" style="margin-top:6px; color:#1e40af;">
              Payment is held in escrow until admin/reviewer resolution.
            </div>
          `}
        </div>
      `;
    } else if (isDisputeEligible) {
      html += `
        <div style="background:#f8fafc; border:1px dashed #cbd5e1; padding:12px; border-radius:8px; margin-top:12px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
              <strong>24-Hour Dispute Window Active</strong>
              <div class="small-note">You may report damaged or missing goods within 24 hours of delivery.</div>
            </div>
            <button class="btn secondary small" onclick="toggleDisputeForm('${order.id}')">
              Report Issue / Dispute
            </button>
          </div>

          <div id="dispute-form-container-${order.id}" style="display:none; margin-top:14px; border-top:1px solid #e2e8f0; padding-top:12px;">
            <h4>File a Delivery Dispute</h4>
            <label>Dispute Reason</label>
            <select id="disp-reason-${order.id}">
              <option value="DAMAGED_GOODS">Damaged Goods / Spoilage</option>
              <option value="WRONG_ITEM">Wrong Item Delivered</option>
              <option value="MISSING_ITEM">Missing Item(s)</option>
              <option value="QUALITY_ISSUE">Substandard Quality</option>
              <option value="LATE_DELIVERY">Unacceptable Delivery Delay</option>
              <option value="OTHER">Other Issue</option>
            </select>

            <label style="margin-top:8px;">Detailed Description</label>
            <textarea id="disp-desc-${order.id}" rows="3" placeholder="Explain the defect, missing items, or delivery problem..."></textarea>

            <label style="margin-top:8px;">Photo Evidence (JPEG, PNG, WebP — Max 5MB)</label>
            <input type="file" id="disp-file-${order.id}" accept="image/jpeg,image/png,image/webp">

            <button class="btn small" style="margin-top:12px;" onclick="submitOrderDispute('${order.id}')">
              Submit Dispute
            </button>
            <div id="disp-msg-${order.id}"></div>
          </div>
        </div>
      `;
    } else {
      html += `
        <div class="small-note" style="margin-top:8px; color:var(--paper-dim);">
          Dispute window closed (24 hours elapsed since delivery).
        </div>
      `;
    }
  }

  box.innerHTML = html;
}

async function cancelBuyerOrder(orderId) {
  if (!confirm("Are you sure you want to cancel this order? Reserved inventory will be restored.")) return;
  try {
    await apiRequest(`/orders/${orderId}/cancel`, {
      method: "POST",
      body: { reason: "Cancelled by buyer" }
    });
    alert("Order cancelled successfully.");
    loadOrders();
  } catch(err) {
    alert(`Cancellation error: ${err.message}`);
  }
}

async function confirmReceiverReceipt(deliveryId, orderId) {
  try {
    await apiRequest(`/logistics/deliveries/${deliveryId}/confirm-receipt`, {
      method: "POST",
      body: { notes: "Receiver verified delivery at destination" }
    });
    alert("Delivery confirmed! Your 24-hour buyer protection and dispute window is now active.");
    loadOrders();
  } catch(err) {
    alert(`Confirmation error: ${err.message}`);
  }
}

function toggleDisputeForm(orderId) {
  const container = document.getElementById(`dispute-form-container-${orderId}`);
  if (container) {
    container.style.display = container.style.display === "none" ? "block" : "none";
  }
}

async function submitOrderDispute(orderId) {
  const reason = document.getElementById(`disp-reason-${orderId}`).value;
  const desc = document.getElementById(`disp-desc-${orderId}`).value.trim();
  const fileInput = document.getElementById(`disp-file-${orderId}`);
  const msgDiv = document.getElementById(`disp-msg-${orderId}`);
  msgDiv.innerHTML = "";

  if (!desc) {
    msgDiv.innerHTML = `<div class="error-box">Please provide a description of the issue.</div>`;
    return;
  }

  const evidenceUrls = [];

  // Upload photo evidence if attached
  if (fileInput && fileInput.files && fileInput.files[0]) {
    msgDiv.innerHTML = `<p class="small-note">Uploading photo evidence...</p>`;
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    try {
      const uploadRes = await apiRequest("/disputes/evidence/upload", {
        method: "POST",
        body: formData,
      });
      evidenceUrls.push(uploadRes.url);
    } catch(err) {
      msgDiv.innerHTML = `<div class="error-box">Photo upload failed: ${err.message}</div>`;
      return;
    }
  }

  try {
    msgDiv.innerHTML = `<p class="small-note">Filing dispute with operations team...</p>`;
    await apiRequest("/disputes", {
      method: "POST",
      body: {
        order_id: orderId,
        reason: reason,
        description: desc,
        evidence_urls: evidenceUrls
      }
    });
    msgDiv.innerHTML = `<div class="success-box">Dispute filed successfully! Payment is held pending review.</div>`;
    setTimeout(() => loadOrders(), 1500);
  } catch(err) {
    msgDiv.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}


// ============================================================
// LOGISTICS SECTION
// ============================================================

async function initLogistics() {
  document.getElementById("logistics-view").style.display = "block";

  const partnerForm = document.getElementById("partner-form");
  if (partnerForm) {
    partnerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const msg = document.getElementById("partner-msg");
      msg.innerHTML = "";
      try {
        await apiRequest("/logistics-partners", {
          method: "POST",
          body: {
            name: document.getElementById("lp-name").value,
            vehicle_type: document.getElementById("lp-vehicle").value,
            capacity_kg: parseFloat(document.getElementById("lp-capacity").value),
            cost_per_km: parseFloat(document.getElementById("lp-cost-km").value),
            base_cost: parseFloat(document.getElementById("lp-base-cost").value || 0),
            supports_cold_chain: document.getElementById("lp-cold-chain").checked,
            current_location: document.getElementById("lp-location").value || null,
          },
        });
        msg.innerHTML = `<div class="success-box">Partner added.</div>`;
        partnerForm.reset();
        loadPartners();
      } catch(err) {
        msg.innerHTML = `<div class="error-box">${err.message}</div>`;
      }
    });
  }

  loadPartners();
  loadLogisticsBatches();
  loadLogisticsOrders();
}

async function loadPartners() {
  const body = document.getElementById("partners-body");
  if (!body) return;
  try {
    const partners = await apiRequest("/logistics-partners");
    body.innerHTML = partners.map(p => `
      <tr><td>${p.name}</td><td>${p.vehicle_type}</td><td>${p.capacity_kg} kg</td><td>₹${p.cost_per_km}</td></tr>
    `).join("") || `<tr><td colspan="4" class="small-note">No partners yet.</td></tr>`;
  } catch(err) {
    body.innerHTML = `<tr><td colspan="4" class="error-box">${err.message}</td></tr>`;
  }
}

async function loadLogisticsBatches() {
  const list = document.getElementById("logistics-batches-list");
  if (!list) return;
  list.innerHTML = `<p class="small-note">Loading batches...</p>`;

  try {
    const batches = await apiRequest("/logistics/batches");
    if (!batches || !batches.length) {
      list.innerHTML = `<p class="small-note">No delivery batches currently active.</p>`;
      return;
    }

    list.innerHTML = batches.map(b => {
      const weightPct = Math.min(100, Math.round((b.total_weight_kg / (b.max_weight_kg || 500)) * 100));
      const orderPct = Math.min(100, Math.round((b.order_count / (b.max_orders || 50)) * 100));
      return `
        <div class="card" style="margin-bottom:12px; background:#ffffff;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
              <strong>Batch #${b.batch_code || b.id.slice(0,8)}</strong>
              <div class="small-note">Zone: ${b.zone_code || "Zone A"} · Mode: ${b.delivery_mode === "shared_drop_point" ? "Shared Drop Point" : "Home Delivery"} · Slot: ${b.delivery_slot}</div>
            </div>
            <span class="badge">${b.status}</span>
          </div>

          <div style="margin-top:10px;">
            <div style="display:flex; justify-content:space-between; font-size:0.82rem; margin-bottom:4px;">
              <span>Weight Capacity: <strong>${Number(b.total_weight_kg).toFixed(1)} / ${b.max_weight_kg} kg</strong></span>
              <span>${weightPct}%</span>
            </div>
            <div style="background:#e2e8f0; border-radius:6px; height:8px; overflow:hidden;">
              <div style="background:var(--wheat); width:${weightPct}%; height:100%;"></div>
            </div>
          </div>

          <div style="margin-top:8px;">
            <div style="display:flex; justify-content:space-between; font-size:0.82rem; margin-bottom:4px;">
              <span>Order Capacity: <strong>${b.order_count} / ${b.max_orders} orders</strong></span>
              <span>${orderPct}%</span>
            </div>
            <div style="background:#e2e8f0; border-radius:6px; height:8px; overflow:hidden;">
              <div style="background:var(--leaf); width:${orderPct}%; height:100%;"></div>
            </div>
          </div>

          ${b.cutoff_time ? `
            <div class="small-note" style="margin-top:8px;">
              Cutoff schedule: ${new Date(b.cutoff_time).toLocaleString()}
            </div>
          ` : ""}
        </div>
      `;
    }).join("");
  } catch(err) {
    list.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}

async function loadLogisticsOrders() {
  const list = document.getElementById("logistics-orders");
  if (!list) return;
  list.innerHTML = `<p class="small-note">Loading deliveries...</p>`;

  try {
    const orders = await apiRequest("/orders/logistics");
    if (!orders || !orders.length) {
      list.innerHTML = `<p class="small-note">No deliveries currently assigned.</p>`;
      return;
    }

    list.innerHTML = orders.map(o => {
      const normStatus = (o.status || "").toLowerCase();
      let actionHtml = "";
      if (normStatus === "processing" || normStatus === "confirmed") {
        actionHtml = `
          <button class="btn small" style="margin-top:8px;" onclick="advanceOrderStatus('${o.id}', 'shipped')">
            Mark Shipped / Out for Delivery
          </button>
        `;
      } else if (normStatus === "shipped") {
        actionHtml = `
          <button class="btn small secondary" style="margin-top:8px;" onclick="advanceOrderStatus('${o.id}', 'delivered')">
            Mark Delivered at Destination
          </button>
        `;
      }

      return `
        <div class="order-row" style="margin-bottom:16px;">
          <div class="order-row-head">
            <div>
              <strong>Order #${o.id.slice(0,8)}</strong> · Type: ${o.order_type}
            </div>
            <span class="badge">${o.status}</span>
          </div>
          <div class="small-note">
            Deliver to: ${o.delivery_location} ${o.delivery_pincode ? `(PIN: ${o.delivery_pincode})` : ""} · Slot: ${o.delivery_slot}
          </div>
          <div style="margin-top:8px;">
            <strong>Total: ₹${Number(o.total_amount).toFixed(2)}</strong>
          </div>
          <div id="logistics-extra-${o.id}" style="margin-top:10px;">
            ${actionHtml}
          </div>
        </div>
      `;
    }).join("");

  } catch(err) {
    list.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}


// ============================================================
// ADMIN & REVIEWER SECTION
// ============================================================

async function initAdmin() {
  document.getElementById("admin-view").style.display = "block";

  // Tab switching
  document.querySelectorAll("[data-atab]").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll("[data-atab]").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      ["disputes", "zones", "droppoints", "batches", "ledger"].forEach(name => {
        const el = document.getElementById(`atab-${name}`);
        if (el) el.style.display = (name === tab.dataset.atab) ? "block" : "none";
      });

      if (tab.dataset.atab === "disputes") loadAdminDisputes();
      if (tab.dataset.atab === "zones") loadAdminZones();
      if (tab.dataset.atab === "droppoints") loadAdminDropPoints();
      if (tab.dataset.atab === "batches") loadAdminBatches();
      if (tab.dataset.atab === "ledger") loadAdminLedger();
    });
  });

  // Setup form submissions
  setupAdminForms();

  // Load initial view
  loadAdminDisputes();
}

function setupAdminForms() {
  // Create Delivery Zone
  const zoneForm = document.getElementById("admin-zone-form");
  if (zoneForm) {
    zoneForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const msg = document.getElementById("admin-zone-msg");
      msg.innerHTML = "";
      try {
        const pincodesStr = document.getElementById("az-pincodes").value;
        const pincodes = pincodesStr.split(",").map(s => s.trim()).filter(Boolean);
        await apiRequest("/logistics/zones", {
          method: "POST",
          body: {
            code: document.getElementById("az-code").value.trim().toUpperCase(),
            name: document.getElementById("az-name").value.trim(),
            state: document.getElementById("az-state").value.trim(),
            covered_pincodes: pincodes,
            min_weight_threshold_kg: parseFloat(document.getElementById("az-min-weight").value),
            max_weight_capacity_kg: parseFloat(document.getElementById("az-max-weight").value),
            max_orders_per_batch: parseInt(document.getElementById("az-max-orders").value, 10),
            dispatch_buffer_minutes: parseInt(document.getElementById("az-dispatch-buffer").value, 10),
            home_delivery_enabled: document.getElementById("az-home-del").checked,
            drop_point_enabled: document.getElementById("az-drop-point").checked,
          }
        });
        msg.innerHTML = `<div class="success-box">Delivery zone registered!</div>`;
        zoneForm.reset();
        loadAdminZones();
      } catch(err) {
        msg.innerHTML = `<div class="error-box">${err.message}</div>`;
      }
    });
  }

  // Create Shared Drop Point
  const dpForm = document.getElementById("admin-droppoint-form");
  if (dpForm) {
    dpForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const msg = document.getElementById("admin-droppoint-msg");
      msg.innerHTML = "";
      try {
        await apiRequest("/logistics/drop-points", {
          method: "POST",
          body: {
            name: document.getElementById("adp-name").value.trim(),
            code: document.getElementById("adp-code").value.trim().toUpperCase(),
            pincode: document.getElementById("adp-pincode").value.trim(),
            physical_address: document.getElementById("adp-address").value.trim(),
            operating_hours: document.getElementById("adp-hours").value.trim(),
            capacity_orders: parseInt(document.getElementById("adp-capacity").value, 10),
            contact_person: document.getElementById("adp-contact").value.trim() || null,
            contact_phone: document.getElementById("adp-phone").value.trim() || null,
          }
        });
        msg.innerHTML = `<div class="success-box">Shared drop point created!</div>`;
        dpForm.reset();
        loadAdminDropPoints();
      } catch(err) {
        msg.innerHTML = `<div class="error-box">${err.message}</div>`;
      }
    });
  }
}

// ---------------- ADMIN DISPUTES ----------------
async function loadAdminDisputes() {
  const container = document.getElementById("admin-disputes-list");
  if (!container) return;
  container.innerHTML = `<p class="small-note">Loading disputes...</p>`;

  try {
    const disputes = await apiRequest("/disputes");
    if (!disputes || !disputes.length) {
      container.innerHTML = `<p class="small-note">No disputes on record.</p>`;
      return;
    }

    container.innerHTML = disputes.map(d => {
      const isPending = d.status === "PENDING_REVIEW" || d.status === "IN_REVIEW";
      return `
        <div class="card" style="margin-bottom:16px;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
              <strong>Dispute #${d.id.slice(0,8)}</strong> · Order #${d.order_id.slice(0,8)}
              <div class="small-note">Filed on: ${new Date(d.created_at).toLocaleString()} · Reason: <strong>${d.reason}</strong></div>
            </div>
            <span class="badge" style="${d.status === 'RESOLVED' ? 'background:#dcfce7; color:#15803d;' : 'background:#fee2e2; color:#991b1b;'}">
              ${d.status}
            </span>
          </div>

          <div style="margin-top:10px; background:#f8fafc; padding:10px; border-radius:8px; font-size:0.9rem;">
            <strong>Buyer Description:</strong> "${d.description}"
          </div>

          ${d.evidence && d.evidence.length ? `
            <div style="margin-top:10px;">
              <strong>Photo Evidence:</strong>
              <div style="display:flex; gap:10px; margin-top:6px; flex-wrap:wrap;">
                ${d.evidence.map(e => `
                  <a href="${API_BASE}${e.file_url}" target="_blank" style="display:inline-block; border:1px solid #cbd5e1; border-radius:8px; overflow:hidden;">
                    <img src="${API_BASE}${e.file_url}" style="width:100px; height:80px; object-fit:cover; display:block;">
                  </a>
                `).join("")}
              </div>
            </div>
          ` : ""}

          ${d.resolution ? `
            <div style="margin-top:12px; background:#f0fdf4; padding:10px; border-radius:8px;">
              <strong>Resolution: ${d.resolution}</strong>
              <div class="small-note">Reviewer notes: "${d.reviewer_notes || 'No notes'}"</div>
            </div>
          ` : ""}

          ${isPending ? `
            <div style="margin-top:14px; border-top:1px solid #e2e8f0; padding-top:12px;">
              <label>Reviewer Notes / Justification</label>
              <input type="text" id="admin-rev-note-${d.id}" placeholder="e.g. Photo confirms spoilage in transit, approved full refund.">

              <div style="display:flex; gap:10px; margin-top:10px;">
                <button class="btn small" style="background:#dc2626;" onclick="resolveDispute('${d.id}', 'REFUND')">
                  Resolve: Refund Buyer
                </button>
                <button class="btn small" onclick="resolveDispute('${d.id}', 'RELEASE')">
                  Resolve: Release Payout
                </button>
                <button class="btn small secondary" onclick="resolveDispute('${d.id}', 'REJECTED')">
                  Reject Dispute
                </button>
              </div>
            </div>
          ` : ""}
        </div>
      `;
    }).join("");

  } catch(err) {
    container.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}

async function resolveDispute(disputeId, resolution) {
  const notesInput = document.getElementById(`admin-rev-note-${disputeId}`);
  const notes = notesInput ? notesInput.value.trim() : "";
  if (!confirm(`Are you sure you want to mark this dispute as ${resolution}?`)) return;

  try {
    await apiRequest(`/disputes/${disputeId}/resolve`, {
      method: "POST",
      body: {
        resolution: resolution,
        reviewer_notes: notes || `Resolved as ${resolution} by reviewer`
      }
    });
    alert(`Dispute #${disputeId.slice(0,8)} successfully resolved as ${resolution}.`);
    loadAdminDisputes();
  } catch(err) {
    alert(`Resolution error: ${err.message}`);
  }
}

// ---------------- ADMIN ZONES ----------------
async function loadAdminZones() {
  const container = document.getElementById("admin-zones-table");
  if (!container) return;
  container.innerHTML = `<p class="small-note">Loading zones...</p>`;

  try {
    const zones = await apiRequest("/logistics/zones");
    if (!zones || !zones.length) {
      container.innerHTML = `<p class="small-note">No delivery zones registered yet.</p>`;
      return;
    }

    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>State</th>
            <th>PINs</th>
            <th>Capacities</th>
            <th>Active</th>
          </tr>
        </thead>
        <tbody>
          ${zones.map(z => `
            <tr>
              <td><strong>${z.code}</strong></td>
              <td>${z.name}</td>
              <td>${z.state}</td>
              <td><span class="small-note">${(z.covered_pincodes || []).join(", ") || "All"}</span></td>
              <td>${z.min_weight_threshold_kg} - ${z.max_weight_capacity_kg} kg</td>
              <td>${z.is_active ? "✓" : "✗"}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  } catch(err) {
    container.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}

// ---------------- ADMIN DROP POINTS ----------------
async function loadAdminDropPoints() {
  const container = document.getElementById("admin-droppoints-table");
  if (!container) return;
  container.innerHTML = `<p class="small-note">Loading drop points...</p>`;

  try {
    const points = await apiRequest("/logistics/drop-points");
    if (!points || !points.length) {
      container.innerHTML = `<p class="small-note">No shared drop points registered yet.</p>`;
      return;
    }

    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Code</th>
            <th>Name</th>
            <th>PIN</th>
            <th>Address</th>
            <th>Capacity</th>
            <th>Active</th>
          </tr>
        </thead>
        <tbody>
          ${points.map(p => `
            <tr>
              <td><strong>${p.code}</strong></td>
              <td>${p.name}</td>
              <td>${p.pincode}</td>
              <td>${p.physical_address}</td>
              <td>${p.capacity_orders} orders</td>
              <td>${p.is_active ? "✓" : "✗"}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  } catch(err) {
    container.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}

// ---------------- ADMIN BATCHES ----------------
async function loadAdminBatches() {
  const container = document.getElementById("admin-batches-list");
  if (!container) return;
  container.innerHTML = `<p class="small-note">Loading batches...</p>`;

  try {
    const batches = await apiRequest("/logistics/batches");
    if (!batches || !batches.length) {
      container.innerHTML = `<p class="small-note">No batches currently exist.</p>`;
      return;
    }

    container.innerHTML = batches.map(b => `
      <div class="card" style="margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <div>
            <strong>Batch #${b.batch_code || b.id.slice(0,8)}</strong>
            <div class="small-note">Zone: ${b.zone_code || "Zone A"} · Mode: ${b.delivery_mode} · Slot: ${b.delivery_slot}</div>
          </div>
          <span class="badge">${b.status}</span>
        </div>
        <div style="display:flex; gap:20px; margin-top:10px; font-size:0.88rem;">
          <div>Weight: <strong>${Number(b.total_weight_kg).toFixed(1)} / ${b.max_weight_kg} kg</strong></div>
          <div>Orders: <strong>${b.order_count} / ${b.max_orders}</strong></div>
          <div>Cutoff: <strong>${b.cutoff_time ? new Date(b.cutoff_time).toLocaleTimeString() : 'N/A'}</strong></div>
        </div>
      </div>
    `).join("");
  } catch(err) {
    container.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}

async function triggerEvaluateCutoffs() {
  try {
    const res = await apiRequest("/logistics/batches/evaluate-cutoffs", { method: "POST" });
    alert(`Evaluated ${res.evaluated_count} batches: ${res.dispatched_count} dispatched, ${res.flagged_for_review_count} flagged below-threshold.`);
    loadAdminBatches();
  } catch(err) {
    alert(`Evaluation error: ${err.message}`);
  }
}

// ---------------- ADMIN LEDGER ----------------
async function loadAdminLedger() {
  const container = document.getElementById("admin-ledger-table");
  if (!container) return;
  container.innerHTML = `<p class="small-note">Loading financial ledger...</p>`;

  try {
    const entries = await apiRequest("/payments/ledger");
    if (!entries || !entries.length) {
      container.innerHTML = `<p class="small-note">No ledger entries recorded yet.</p>`;
      return;
    }

    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Entry ID</th>
            <th>Payment ID</th>
            <th>Order ID</th>
            <th>Type</th>
            <th>Amount (₹)</th>
            <th>Description</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          ${entries.map(e => `
            <tr>
              <td><code>${e.id.slice(0,8)}</code></td>
              <td><code>${e.payment_id ? e.payment_id.slice(0,8) : '—'}</code></td>
              <td><code>${e.order_id ? e.order_id.slice(0,8) : '—'}</code></td>
              <td><span class="badge" style="font-size:0.75rem;">${e.entry_type}</span></td>
              <td><strong>₹${Number(e.amount).toFixed(2)}</strong></td>
              <td><span class="small-note">${e.description}</span></td>
              <td><span class="small-note">${new Date(e.created_at).toLocaleString()}</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  } catch(err) {
    container.innerHTML = `<div class="error-box">${err.message}</div>`;
  }
}


// ============================================================
// ROUTER INITIALIZATION
// ============================================================

if (user.role === "farmer") {
  initFarmer();
} else if (user.role === "buyer") {
  initBuyer();
} else if (user.role === "logistics") {
  initLogistics();
} else if (user.role === "admin" || user.role === "reviewer") {
  initAdmin();
  // Also initialize logistics view for admins
  initLogistics();
}
