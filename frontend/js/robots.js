/* Fleet registry: company-scoped robot list with debounced search. */

(() => {
  const Fleet = window.Fleet;
  const main = document.getElementById("main");
  if (!Fleet || !main) return;

  const user = Fleet.user();
  const isAdmin = user && user.role === "admin";

  main.innerHTML = `
    <div class="app">
      <header class="app-head">
        <div class="app-head__copy">
          <p class="eyebrow">Module 01 <span class="eyebrow__sep">/</span> Registry</p>
          <h1 class="app-title">Fleet registry</h1>
          <p class="app-lede">
            Every robot registered to your company, with the latest status and
            battery. A unit with no recent sample reads offline, never stale.
          </p>
        </div>
        <div class="app-actions">
          ${
            isAdmin
              ? `<a class="btn btn--dark" href="/robot-new.html">Register robot <span class="btn__arrow" aria-hidden="true">→</span></a>`
              : ""
          }
          <a class="btn btn--ghost" href="/map.html">Open live map</a>
        </div>
      </header>

      <section class="app-section" aria-labelledby="registry-title">
        <div class="toolbar">
          <label class="search">
            <span class="sr-only">Search robots by name</span>
            <input class="input" id="search" type="search" placeholder="Search by name…" autocomplete="off" />
          </label>
          <span class="toolbar__spacer"></span>
          <span class="app-note" id="count" aria-live="polite"></span>
        </div>

        <div id="notice" class="app-section"></div>

        <div class="table-card" id="registry" aria-labelledby="registry-title">
          <p class="state" role="status">Loading robots…</p>
        </div>
      </section>
    </div>`;

  const search = document.getElementById("search");
  const body = document.getElementById("registry");
  const count = document.getElementById("count");
  const notice = document.getElementById("notice");

  let timer = null;
  let lastQuery = "";

  function tableHTML(robots) {
    const rows = robots
      .map(
        (robot) => `
        <tr>
          <td>
            <span class="cell-name">${Fleet.escapeHtml(robot.name)}</span>
            <span class="cell-sub">${Fleet.escapeHtml(robot.serial_number)}</span>
          </td>
          <td>${Fleet.statusChip(robot.status)}</td>
          <td>${Fleet.batteryBadge(robot.battery_pct, robot.status)}</td>
          <td class="num" title="${Fleet.escapeHtml(robot.last_seen || "")}">
            ${robot.last_seen ? Fleet.relative(robot.last_seen) : "never"}
            <span class="cell-sub">${robot.last_seen ? Fleet.formatTime(robot.last_seen, true) : "no telemetry"}</span>
          </td>
        </tr>`,
      )
      .join("");

    return `
      <div class="table-wrap">
        <table class="data-table">
          <caption class="sr-only">Robots in your company</caption>
          <thead>
            <tr>
              <th scope="col">Name</th>
              <th scope="col">Status</th>
              <th scope="col">Battery</th>
              <th scope="col">Last seen</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  function render(robots) {
    if (!robots.length) {
      count.textContent = "0 robots";
      Fleet.empty(
        body,
        lastQuery
          ? `No robots match “${lastQuery}”.`
          : "No robots yet. An admin can register the first unit.",
      );
      return;
    }
    count.textContent = `${robots.length} robot${robots.length === 1 ? "" : "s"}`;
    body.innerHTML = tableHTML(robots);
  }

  async function load({ showLoading = true } = {}) {
    if (showLoading) Fleet.loading(body, "Loading robots…");
    Fleet.notice(notice, "");
    const query = search.value.trim();
    lastQuery = query;

    try {
      const robots = await Fleet.api(
        `/api/v1/robots${query ? `?search=${encodeURIComponent(query)}` : ""}`,
      );
      render(robots);
    } catch (error) {
      Fleet.errorState(body, error.message || "Could not load the fleet.");
      count.textContent = "";
    }
  }

  search.addEventListener("input", () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => load(), 300);
  });

  load();
  window.setInterval(() => load({ showLoading: false }), 10000);
})();
