/* Session, API access, and shared render helpers. */

(() => {
  const TOKEN_KEY = "fleet.token";
  const USER_KEY = "fleet.user";

  function token() {
    return window.localStorage.getItem(TOKEN_KEY) || "";
  }

  function user() {
    try {
      return JSON.parse(window.localStorage.getItem(USER_KEY) || "null");
    } catch {
      return null;
    }
  }

  function saveSession(payload) {
    window.localStorage.setItem(TOKEN_KEY, payload.access_token);
    window.localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
  }

  function clearSession() {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
  }

  function loginRedirect() {
    const next = `${window.location.pathname}${window.location.search}`;
    window.location.replace(`/login.html?next=${encodeURIComponent(next)}`);
  }

  class ApiError extends Error {
    constructor(message, status) {
      super(message);
      this.status = status;
    }
  }

  async function request(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const hasBody = options.body !== undefined;
    if (hasBody) headers["Content-Type"] = "application/json";

    const current = token();
    if (current) headers.Authorization = `Bearer ${current}`;

    let response;
    try {
      response = await fetch(path, { ...options, headers });
    } catch {
      throw new ApiError("Cannot reach the server. Is the API running?", 0);
    }

    if (response.status === 401) {
      clearSession();
      if (!path.endsWith("/auth/login")) loginRedirect();
      throw new ApiError("Your session expired. Log in again.", 401);
    }

    let body = null;
    if (response.status !== 204) {
      body = await response.json().catch(() => null);
    }

    if (!response.ok) {
      const detail = body && body.detail;
      let message = "Something went wrong. Try again.";
      if (typeof detail === "string") message = detail;
      else if (Array.isArray(detail) && detail.length) {
        message = detail.map((item) => item.msg).join("; ");
      }
      throw new ApiError(message, response.status);
    }
    return body;
  }

  function logout() {
    clearSession();
    window.location.replace("/login.html");
  }

  /* Dates: stored in UTC, displayed in the browser's local time. */

  function formatTime(value, withDate = false) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "—";
    const time = new Intl.DateTimeFormat(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(date);
    if (!withDate) return time;
    const day = new Intl.DateTimeFormat(undefined, {
      day: "2-digit",
      month: "short",
    }).format(date);
    return `${day} · ${time}`;
  }

  function formatLocalHour(iso) {
    return new Intl.DateTimeFormat(undefined, { hour: "2-digit", hour12: false }).format(
      new Date(iso),
    );
  }

  function relative(value) {
    if (!value) return "never";
    const seconds = Math.max(0, (Date.now() - new Date(value).getTime()) / 1000);
    if (seconds < 60) return `${Math.round(seconds)}s ago`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.round(seconds / 3600)}h ago`;
    return `${Math.round(seconds / 86400)}d ago`;
  }

  /* Markup helpers */

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  const STATUS_LABEL = { active: "Active", idle: "Idle", offline: "Offline" };

  function statusChip(status) {
    const modifier =
      status === "active" ? "chip--ready" : status === "offline" ? "chip--danger" : "chip--queued";
    return `<span class="chip ${modifier}"><span class="status-dot ${status === "active" ? "status-dot--live" : "status-dot--off"}" aria-hidden="true"></span>${STATUS_LABEL[status] || status}</span>`;
  }

  function batteryBadge(percentage, status) {
    if (status === "offline" || percentage === null || percentage === undefined) {
      return `<span class="battery-badge battery-badge--unknown">unknown</span>`;
    }
    const value = Math.max(0, Math.min(100, Number(percentage)));
    const tone = value < 20 ? "low" : value <= 50 ? "mid" : "high";
    return `
      <span class="battery-badge battery-badge--${tone}">
        <span class="battery-badge__bar" aria-hidden="true"><span style="width:${value}%"></span></span>
        <span class="battery-badge__value">${value.toFixed(0)}%</span>
      </span>`;
  }

  function missionChip(status) {
    const modifier =
      status === "running"
        ? "chip--live"
        : status === "completed"
          ? "chip--ready"
          : status === "stopped"
            ? "chip--danger"
            : "chip--queued";
    return `<span class="chip ${modifier}">${escapeHtml(status)}</span>`;
  }

  function alertChip(type) {
    return `<span class="chip ${type === "intrusion" ? "chip--danger" : "chip--warn"}">${escapeHtml(type)}</span>`;
  }

  function notice(container, message, tone = "error") {
    if (!container) return;
    container.innerHTML = message
      ? `<p class="notice notice--${tone}" role="${tone === "error" ? "alert" : "status"}">${escapeHtml(message)}</p>`
      : "";
  }

  function loading(container, label = "Loading…") {
    if (container) {
      container.innerHTML = `<p class="state state--loading" role="status">${escapeHtml(label)}</p>`;
    }
  }

  function empty(container, message) {
    if (container) {
      container.innerHTML = `<p class="state state--empty">${escapeHtml(message)}</p>`;
    }
  }

  function errorState(container, message) {
    if (container) {
      container.innerHTML = `<p class="state state--error" role="alert">${escapeHtml(message)}</p>`;
    }
  }

  window.Fleet = {
    ApiError,
    api: request,
    token,
    user,
    saveSession,
    clearSession,
    logout,
    formatTime,
    formatLocalHour,
    relative,
    escapeHtml,
    statusChip,
    batteryBadge,
    missionChip,
    alertChip,
    notice,
    loading,
    empty,
    errorState,
  };
})();
