/**
 * ==========================================================================
 * SMART PERSONAL FINANCE DASHBOARD - AUTHENTICATION CONTROLLER
 * Real FastAPI Registration, Login, JWT session management & UI validation
 * ==========================================================================
 */

document.addEventListener("DOMContentLoaded", () => {
  initAuthPage();
});

function initAuthPage() {
  initTheme();
  setupLoginForm();
  setupRegisterForm();
  setupDemoLoginHelper();
}

/**
 * Validate email format
 */
function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(String(email).toLowerCase());
}

/**
 * Calculate password strength score (0 to 4)
 */
function evaluatePasswordStrength(password) {
  let score = 0;
  if (!password) return { score: 0, text: "Too short", class: "rose" };

  if (password.length >= 8) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^a-zA-Z\d]/.test(password)) score++;

  if (score === 4) return { score, text: "Strong", class: "emerald" };
  if (score === 3) return { score, text: "Good", class: "indigo" };
  if (score === 2) return { score, text: "Fair", class: "amber" };
  return { score, text: "Weak", class: "rose" };
}

/**
 * Setup Login Form Handling with FastAPI backend
 */
function setupLoginForm() {
  const form = document.getElementById("login-form");
  if (!form) return;

  const emailInput = document.getElementById("login-email");
  const passwordInput = document.getElementById("login-password");
  const emailError = document.getElementById("login-email-error");
  const passwordError = document.getElementById("login-password-error");
  const submitBtn = form.querySelector("button[type='submit']");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    let hasError = false;

    // Reset errors
    if (emailError) {
      emailError.textContent = "";
      emailError.classList.remove("visible");
    }
    if (passwordError) {
      passwordError.textContent = "";
      passwordError.classList.remove("visible");
    }

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!email || !isValidEmail(email)) {
      if (emailError) {
        emailError.textContent = "Please enter a valid email address.";
        emailError.classList.add("visible");
      }
      hasError = true;
    }

    if (!password) {
      if (passwordError) {
        passwordError.textContent = "Please enter your password.";
        passwordError.classList.add("visible");
      }
      hasError = true;
    }

    if (hasError) return;

    // Disable button during network request
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Signing In...";
    }

    try {
      const response = await apiPost("/auth/login", { email, password });
      const token = response.data?.access_token;
      const user = response.data?.user;

      if (!token) {
        throw new Error("Authentication response did not contain an access token.");
      }

      // Store safe user data and JWT token (no passwords)
      setAuthSession(token, user);
      showToast("Login Successful", `Welcome back, ${user.name}!`, "success");

      setTimeout(() => {
        window.location.href = "index.html";
      }, 500);
    } catch (err) {
      console.error("Login failed:", err);
      if (passwordError) {
        passwordError.textContent = err.message || "Invalid credentials. Please check and try again.";
        passwordError.classList.add("visible");
      }
      showToast("Sign In Failed", err.message || "Invalid email or password", "danger");
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Sign In to Dashboard";
      }
    }
  });
}

/**
 * Setup Register Form Handling with FastAPI backend
 */
function setupRegisterForm() {
  const form = document.getElementById("register-form");
  if (!form) return;

  const nameInput = document.getElementById("reg-name");
  const emailInput = document.getElementById("reg-email");
  const passwordInput = document.getElementById("reg-password");
  const confirmPasswordInput = document.getElementById("reg-confirm-password");
  const strengthMeter = document.getElementById("password-strength-fill");
  const strengthText = document.getElementById("password-strength-text");
  const submitBtn = form.querySelector("button[type='submit']");

  // Dynamic Password Strength Meter
  if (passwordInput && strengthMeter && strengthText) {
    passwordInput.addEventListener("input", (e) => {
      const val = e.target.value;
      const strength = evaluatePasswordStrength(val);

      const percent = (strength.score / 4) * 100;
      strengthMeter.style.width = `${percent}%`;

      if (strength.class === "emerald") strengthMeter.style.background = "var(--emerald)";
      else if (strength.class === "indigo") strengthMeter.style.background = "var(--indigo)";
      else if (strength.class === "amber") strengthMeter.style.background = "var(--amber)";
      else strengthMeter.style.background = "var(--rose)";

      strengthText.textContent = val ? `Strength: ${strength.text}` : "";
    });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    let hasError = false;

    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    const nameError = document.getElementById("reg-name-error");
    const emailError = document.getElementById("reg-email-error");
    const passwordError = document.getElementById("reg-password-error");
    const confirmError = document.getElementById("reg-confirm-error");

    if (nameError) { nameError.textContent = ""; nameError.classList.remove("visible"); }
    if (emailError) { emailError.textContent = ""; emailError.classList.remove("visible"); }
    if (passwordError) { passwordError.textContent = ""; passwordError.classList.remove("visible"); }
    if (confirmError) { confirmError.textContent = ""; confirmError.classList.remove("visible"); }

    if (!name) {
      if (nameError) {
        nameError.textContent = "Please enter your full name.";
        nameError.classList.add("visible");
      }
      hasError = true;
    }

    if (!email || !isValidEmail(email)) {
      if (emailError) {
        emailError.textContent = "Please enter a valid email address.";
        emailError.classList.add("visible");
      }
      hasError = true;
    }

    if (!password || password.length < 8) {
      if (passwordError) {
        passwordError.textContent = "Password must be at least 8 characters.";
        passwordError.classList.add("visible");
      }
      hasError = true;
    }

    if (password !== confirmPassword) {
      if (confirmError) {
        confirmError.textContent = "Passwords do not match.";
        confirmError.classList.add("visible");
      }
      hasError = true;
    }

    if (hasError) return;

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Creating Account...";
    }

    try {
      const response = await apiPost("/auth/register", { name, email, password });
      const token = response.data?.access_token;
      const user = response.data?.user;

      if (!token) {
        throw new Error("Registration response did not contain an access token.");
      }

      setAuthSession(token, user);
      showToast("Account Created", `Welcome to Smart Personal Finance, ${user.name}!`, "success");

      setTimeout(() => {
        window.location.href = "index.html";
      }, 500);
    } catch (err) {
      console.error("Registration failed:", err);
      if (emailError && err.message.toLowerCase().includes("email")) {
        emailError.textContent = err.message;
        emailError.classList.add("visible");
      } else if (passwordError && err.message.toLowerCase().includes("password")) {
        passwordError.textContent = err.message;
        passwordError.classList.add("visible");
      }
      showToast("Registration Failed", err.message || "Failed to create account", "danger");
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Create Free Account";
      }
    }
  });
}

/**
 * One-click demo credentials filler
 */
function setupDemoLoginHelper() {
  const demoBtn = document.getElementById("fill-demo-credentials-btn");
  if (demoBtn) {
    demoBtn.addEventListener("click", () => {
      const emailInput = document.getElementById("login-email");
      const passwordInput = document.getElementById("login-password");
      if (emailInput && passwordInput) {
        emailInput.value = "ansh.test@fintech.dev";
        passwordInput.value = "SecurePass123!";
        showToast("Demo Credentials Loaded", "Click 'Sign In to Dashboard' to continue.", "info");
      }
    });
  }
}
