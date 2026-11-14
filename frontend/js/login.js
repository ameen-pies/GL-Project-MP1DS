/* Login form: authenticate, persist the session, then return to the page asked for. */

(() => {
  const Fleet = window.Fleet;
  if (!Fleet) return;

  const form = document.getElementById("login-form");
  if (!form) return;

  const notice = document.getElementById("login-notice");
  const submit = document.getElementById("login-submit");
  const params = new URLSearchParams(window.location.search);
  const requested = params.get("next") || "";
  const next = requested.startsWith("/") && !requested.startsWith("//") ? requested : "/robots.html";

  if (Fleet.token()) {
    window.location.replace(next);
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    Fleet.notice(notice, "");

    const email = form.email.value.trim();
    const password = form.password.value;

    if (!email || !password) {
      Fleet.notice(notice, "Enter both your email and password.");
      return;
    }

    submit.disabled = true;
    submit.textContent = "Signing in…";

    try {
      const payload = await Fleet.api("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      Fleet.saveSession(payload);
      window.location.replace(next);
    } catch (error) {
      Fleet.notice(notice, error.message || "Login failed. Try again.");
      form.password.select();
    } finally {
      submit.disabled = false;
      submit.textContent = "Log in";
    }
  });
})();
