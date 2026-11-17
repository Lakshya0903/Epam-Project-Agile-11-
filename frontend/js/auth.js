// ============================================================
// FarmCart Authentication Controller
// Manages Login, Registration, Tab switching, and Role-based forms
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  // If already logged in, redirect directly to dashboard
  if (Auth.getToken()) {
    const user = Auth.getUser();
    if (user) {
      window.location.href = "dashboard.html";
      return;
    }
  }

  initTabs();
  initRoleFields();
  initForms();
});

function initTabs() {
  const tabs = document.querySelectorAll(".tabs .tab");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");

      const tabName = tab.dataset.tab;
      if (tabName === "login") {
        loginForm.style.display = "block";
        registerForm.style.display = "none";
      } else {
        loginForm.style.display = "none";
        registerForm.style.display = "block";
      }
    });
  });
}

function initRoleFields() {
  const roleSelect = document.getElementById("reg-role");
  const farmerFields = document.getElementById("farmer-fields");
  const buyerFields = document.getElementById("buyer-fields");

  function updateFields() {
    const role = roleSelect.value;
    if (role === "farmer") {
      farmerFields.style.display = "block";
      buyerFields.style.display = "none";
    } else if (role === "buyer") {
      farmerFields.style.display = "none";
      buyerFields.style.display = "block";
    } else {
      farmerFields.style.display = "none";
      buyerFields.style.display = "none";
    }
  }

  if (roleSelect) {
    roleSelect.addEventListener("change", updateFields);
    updateFields();
  }

  // Also toggle business name if buyer type changes
  const buyerTypeSelect = document.getElementById("reg-buyer-type");
  const businessNameInput = document.getElementById("reg-business-name");
  if (buyerTypeSelect && businessNameInput) {
    buyerTypeSelect.addEventListener("change", () => {
      const isBulk = buyerTypeSelect.value === "bulk";
      businessNameInput.required = isBulk;
    });
  }
}

function initForms() {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const loginError = document.getElementById("login-error");
  const registerError = document.getElementById("register-error");

  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      loginError.innerHTML = "";

      const email = document.getElementById("login-email").value.trim();
      const password = document.getElementById("login-password").value;

      if (!email || !password) {
        loginError.innerHTML = '<div class="error-box">Please provide both email and password.</div>';
        return;
      }

      const submitBtn = loginForm.querySelector("button[type='submit']");
      const originalText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = "Logging in...";

      try {
        const data = await apiRequest("/auth/login", {
          method: "POST",
          body: { username: email, password },
          form: true,
          auth: false,
        });

        Auth.setSession(data.access_token, data.user);
        window.location.href = "dashboard.html";
      } catch (err) {
        loginError.innerHTML = `<div class="error-box">${err.message}</div>`;
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      registerError.innerHTML = "";

      const role = document.getElementById("reg-role").value;
      const name = document.getElementById("reg-name").value.trim();
      const phone = document.getElementById("reg-phone").value.trim();
      const email = document.getElementById("reg-email").value.trim();
      const password = document.getElementById("reg-password").value;

      const payload = {
        name,
        email,
        phone: phone || null,
        password,
        role,
      };

      if (role === "farmer") {
        const farmName = document.getElementById("reg-farm-name")?.value.trim();
        const pickupLoc = document.getElementById("reg-pickup-location")?.value.trim();
        if (!farmName || !pickupLoc) {
          registerError.innerHTML = '<div class="error-box">Farm/FPO name and pickup location are required.</div>';
          return;
        }
        payload.farm_or_fpo_name = farmName;
        payload.pickup_location = pickupLoc;
      } else if (role === "buyer") {
        const buyerType = document.getElementById("reg-buyer-type")?.value;
        const businessName = document.getElementById("reg-business-name")?.value.trim();
        const defaultLoc = document.getElementById("reg-default-location")?.value.trim();
        payload.buyer_type = buyerType;
        payload.business_name = businessName || null;
        payload.default_location = defaultLoc || null;
      }

      const submitBtn = registerForm.querySelector("button[type='submit']");
      const originalText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = "Creating account...";

      try {
        const data = await apiRequest("/auth/register", {
          method: "POST",
          body: payload,
          auth: false,
        });

        Auth.setSession(data.access_token, data.user);
        window.location.href = "dashboard.html";
      } catch (err) {
        registerError.innerHTML = `<div class="error-box">${err.message}</div>`;
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });
  }
}
