/* Alert queue: filter open/all, acknowledge, refresh every 10 seconds. */

(() => {
  const Fleet = window.Fleet;
  const main = document.getElementById("main");
  if (!Fleet || !main) return;

  main.innerHTML = `
    <div class="app">
      <header class="app-head">
        <div class="app-head__copy">
          <p class="eyebrow">Module 04 <span class="eyebrow__sep">/</span> Queue</p>
          <h1 class="app-title">Alerts</h1>
          <p class="app-lede">
            Intrusion and obstacle events raised by robots. Acknowledging an
            alert records who handled it and when; the queue refreshes every ten seconds.
          </p>
        </div>
        <div class="app-actions">
          <span class="metric" style="min-width: 9rem">
            <span class="metric__label">Open now</span>
            <span class="metric__value" id="open-count">—</span>
          </span>
        </div>
      </header>

      <section class="app-section">
        <div class="toolbar">
          <div class="toolbar__group">
            <label class="toolbar__label" for="filter">Show</label>
            <select class="select" id="filter">
              <option value="open" selected>Open alerts</option>
              <option value="all">All alerts</option>
            </select>
          </div>
          <span class="toolbar__spacer"></span>
          <span class="app-note" id="queue-count" aria-live="polite"></span>
        </div>

        <div class="table-card" id="alert-list" style="margin-top: 0.9rem">
          <p class="state" role="status">Loading alerts…</p>
        </div>
        <div id="ack-notice" class="app-section" style="margin-top: 1rem"></div>
      </section>
    </div>`;

  const filter = document.getElementById("filter");
  const list = document.getElementById("alert-list");
  const count = document.getElementById("queue-count");
  const openCount = document.getElementById("open-count");
  const notice = document.getElementById("ack-notice");

  function rowHTML(alert) {
    return `
      <tr>
        <td>
          <span class="cell-name">${Fleet.escapeHtml(alert.robot_name)}</span>
          <span class="cell-sub">${alert.lat.toFixed(4)}, ${alert.lng.toFixed(4)}</span>
        </td>
        <td>${Fleet.alertChip(alert.type)}</td>
        <td class="num">
          ${Fleet.formatTime(alert.ts, true)}
          <span class="cell-sub">${Fleet.relative(alert.ts)}</span>
        </td>
        <td>
          ${
            alert.acknowledged
              ? `<span class="chip chip--ready">acknowledged</span>
                 <span class="cell-sub">${Fleet.escapeHtml(alert.acknowledged_by_name || "unknown")}${
                   alert.acknowledged_at ? ` · ${Fleet.formatTime(alert.acknowledged_at, true)}` : ""
                 }</span>`
              : `<span class="chip chip--warn">open</span>`
          }
        </td>
        <td>
          ${
            alert.acknowledged
              ? `<span class="muted">—</span>`
              : `<button class="btn btn--dark btn--sm" type="button" data-ack="${alert.id}">Acknowledge</button>`
          }
        </td>
      </tr>`;
  }

  function render(alerts) {
    if (!alerts.length) {
      count.textContent = "";
      Fleet.empty(
        list,
        filter.value === "open"
          ? "No open alerts. The queue is clear."
          : "No alerts have been raised for this company yet.",
      );
      return;
    }

    count.textContent = `${alerts.length} alert${alerts.length === 1 ? "" : "s"}`;
    list.innerHTML = `
      <div class="table-wrap">
        <table class="data-table">
          <caption class="sr-only">Alerts raised by robots in your company</caption>
          <thead>
            <tr>
              <th scope="col">Robot / location</th>
              <th scope="col">Type</th>
              <th scope="col">Raised</th>
              <th scope="col">State</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>${alerts.map(rowHTML).join("")}</tbody>
        </table>
      </div>`;

    list.querySelectorAll("[data-ack]").forEach((button) => {
      button.addEventListener("click", async () => {
        button.disabled = true;
        button.textContent = "Saving…";
        Fleet.notice(notice, "");
        try {
          await Fleet.api(`/api/v1/alerts/${button.dataset.ack}/acknowledge`, { method: "POST" });
          Fleet.notice(notice, "Alert acknowledged.", "success");
          await Promise.all([loadAlerts({ showLoading: false }), loadCount()]);
        } catch (error) {
          Fleet.notice(notice, error.message || "Could not acknowledge this alert.");
          button.disabled = false;
          button.textContent = "Acknowledge";
        }
      });
    });
  }

  async function loadAlerts({ showLoading = true } = {}) {
    if (showLoading) Fleet.loading(list, "Loading alerts…");
    try {
      const alerts = await Fleet.api(`/api/v1/alerts?status=${filter.value}`);
      render(alerts);
    } catch (error) {
      Fleet.errorState(list, error.message || "Could not load alerts.");
      count.textContent = "";
    }
  }

  async function loadCount() {
    try {
      const { count: open } = await Fleet.api("/api/v1/alerts/open-count");
      openCount.textContent = String(open);
    } catch {
      openCount.textContent = "—";
    }
  }

  filter.addEventListener("change", () => {
    Fleet.notice(notice, "");
    loadAlerts();
  });

  loadAlerts();
  loadCount();
  window.setInterval(() => {
    loadAlerts({ showLoading: false });
    loadCount();
  }, 10000);
})();
