/* Patrol missions: schedule from a seeded route, start, stop, and read the log. */

(() => {
  const Fleet = window.Fleet;
  const main = document.getElementById("main");
  if (!Fleet || !main) return;

  main.innerHTML = `
    <div class="app">
      <header class="app-head">
        <div class="app-head__copy">
          <p class="eyebrow">Module 03 <span class="eyebrow__sep">/</span> Patrols</p>
          <h1 class="app-title">Patrol missions</h1>
          <p class="app-lede">
            Schedule a mission on a seeded route, then start or stop it. Every
            transition is written to the event log with the operator and the time.
          </p>
        </div>
        <div class="app-actions">
          <a class="btn btn--ghost" href="/map.html">Live map</a>
          <a class="btn btn--ghost" href="/alerts.html">Alert queue</a>
        </div>
      </header>

      <section class="app-section" aria-labelledby="create-title">
        <div class="app-section__head">
          <h2 class="app-section__title" id="create-title">Create a mission</h2>
          <p class="app-note">One running mission per robot</p>
        </div>
        <div class="panel">
          <div id="create-notice"></div>
          <form id="mission-form" novalidate>
            <div class="form-grid">
              <div class="field">
                <label for="robot">Robot</label>
                <select class="select" id="robot" name="robot" required>
                  <option value="">Loading robots…</option>
                </select>
              </div>
              <div class="field">
                <label for="route">Route</label>
                <select class="select" id="route" name="route" required>
                  <option value="">Loading routes…</option>
                </select>
              </div>
              <div class="field field--actions">
                <button class="btn btn--dark" type="submit" id="create-submit">Create mission</button>
              </div>
            </div>
          </form>
        </div>
      </section>

      <section class="app-section" aria-labelledby="list-title">
        <div class="app-section__head">
          <h2 class="app-section__title" id="list-title">Mission queue</h2>
          <span class="app-note" id="mission-count"></span>
        </div>
        <div class="table-card" id="mission-list" aria-labelledby="list-title">
          <p class="state" role="status">Loading missions…</p>
        </div>
      </section>
    </div>`;

  const form = document.getElementById("mission-form");
  const robotSelect = document.getElementById("robot");
  const routeSelect = document.getElementById("route");
  const submit = document.getElementById("create-submit");
  const createNotice = document.getElementById("create-notice");
  const list = document.getElementById("mission-list");
  const count = document.getElementById("mission-count");

  const expanded = new Set();
  let missionCache = [];

  function fillSelect(select, items, emptyLabel, formatter) {
    if (!items.length) {
      select.innerHTML = `<option value="">${emptyLabel}</option>`;
      return;
    }
    select.innerHTML =
      `<option value="">Select…</option>` +
      items.map((item) => `<option value="${item.id}">${Fleet.escapeHtml(formatter(item))}</option>`).join("");
  }

  async function loadOptions() {
    try {
      const [robots, routes] = await Promise.all([
        Fleet.api("/api/v1/robots"),
        Fleet.api("/api/v1/routes"),
      ]);
      fillSelect(robotSelect, robots, "No robots registered", (robot) => `${robot.name} · ${robot.serial_number}`);
      fillSelect(routeSelect, routes, "No routes seeded", (route) => route.name);
      if (!robots.length || !routes.length) {
        Fleet.notice(
          createNotice,
          "A mission needs at least one robot and one route. Register a robot and run the route seed first.",
          "info",
        );
      }
    } catch (error) {
      Fleet.notice(createNotice, error.message || "Could not load robots and routes.");
    }
  }

  function actionsHTML(mission) {
    if (mission.status === "scheduled") {
      return `<button class="btn btn--dark btn--sm" type="button" data-action="start" data-id="${mission.id}">Start</button>`;
    }
    if (mission.status === "running") {
      return `<button class="btn btn--ghost btn--sm" type="button" data-action="stop" data-id="${mission.id}">Stop</button>`;
    }
    return `<span class="muted">—</span>`;
  }

  function eventRows(mission) {
    if (!mission.events.length) {
      return `<li class="muted">No events recorded yet.</li>`;
    }
    return mission.events
      .map(
        (event) => `
        <li>
          ${Fleet.missionChip(event.action === "start" ? "running" : "stopped")}
          <span>${Fleet.escapeHtml(event.user_name || "Unknown user")}</span>
          <span class="mono">${Fleet.formatTime(event.ts, true)}</span>
        </li>`,
      )
      .join("");
  }

  function render(missions) {
    missionCache = missions;
    if (!missions.length) {
      count.textContent = "";
      Fleet.empty(list, "No missions yet. Create one from a seeded route above.");
      return;
    }
    count.textContent = `${missions.length} mission${missions.length === 1 ? "" : "s"}`;

    const rows = missions
      .map((mission) => {
        const open = expanded.has(mission.id);
        return `
          <tr class="${open ? "row--open" : ""}">
            <td>
              <span class="cell-name">${Fleet.escapeHtml(mission.robot_name)}</span>
              <span class="cell-sub">${Fleet.escapeHtml(mission.route_name)}</span>
            </td>
            <td>${Fleet.missionChip(mission.status)}</td>
            <td class="num">${Fleet.formatTime(mission.scheduled_at, true)}</td>
            <td class="num">${
              mission.started_at ? Fleet.formatTime(mission.started_at, true) : "—"
            }</td>
            <td class="num">${
              mission.ended_at ? Fleet.formatTime(mission.ended_at, true) : "—"
            }</td>
            <td>
              <div class="row-actions">
                ${actionsHTML(mission)}
                <button
                  class="btn btn--ghost btn--sm"
                  type="button"
                  data-events="${mission.id}"
                  aria-expanded="${open}"
                >
                  ${open ? "Hide log" : `Log (${mission.events.length})`}
                </button>
              </div>
            </td>
          </tr>
          <tr class="events-row" ${open ? "" : "hidden"} data-events-row="${mission.id}">
            <td colspan="6">
              <ul class="event-list">${eventRows(mission)}</ul>
            </td>
          </tr>`;
      })
      .join("");

    list.innerHTML = `
      <div class="table-wrap">
        <table class="data-table">
          <caption class="sr-only">Patrol missions for your company</caption>
          <thead>
            <tr>
              <th scope="col">Robot / route</th>
              <th scope="col">Status</th>
              <th scope="col">Scheduled</th>
              <th scope="col">Started</th>
              <th scope="col">Ended</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;

    list.querySelectorAll("[data-events]").forEach((button) => {
      button.addEventListener("click", () => {
        const id = Number(button.dataset.events);
        if (expanded.has(id)) expanded.delete(id);
        else expanded.add(id);
        render(missionCache);
      });
    });

    list.querySelectorAll("[data-action]").forEach((button) => {
      button.addEventListener("click", () => transition(button));
    });
  }

  async function transition(button) {
    const id = button.dataset.id;
    const action = button.dataset.action;
    button.disabled = true;
    button.textContent = action === "start" ? "Starting…" : "Stopping…";
    Fleet.notice(createNotice, "");

    try {
      await Fleet.api(`/api/v1/missions/${id}/${action}`, { method: "POST" });
      Fleet.notice(createNotice, `Mission ${action === "start" ? "started" : "stopped"}.`, "success");
      expanded.add(Number(id));
      await loadMissions({ showLoading: false });
    } catch (error) {
      Fleet.notice(createNotice, error.message || `Could not ${action} the mission.`);
      button.disabled = false;
      button.textContent = action === "start" ? "Start" : "Stop";
    }
  }

  async function loadMissions({ showLoading = true } = {}) {
    if (showLoading) Fleet.loading(list, "Loading missions…");
    try {
      const missions = await Fleet.api("/api/v1/missions");
      render(missions);
    } catch (error) {
      Fleet.errorState(list, error.message || "Could not load missions.");
      count.textContent = "";
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    Fleet.notice(createNotice, "");

    const robotId = Number(robotSelect.value);
    const routeId = Number(routeSelect.value);
    if (!robotId || !routeId) {
      Fleet.notice(createNotice, "Choose a robot and a route first.");
      return;
    }

    submit.disabled = true;
    submit.textContent = "Creating…";
    try {
      await Fleet.api("/api/v1/missions", {
        method: "POST",
        body: JSON.stringify({ robot_id: robotId, route_id: routeId }),
      });
      Fleet.notice(createNotice, "Mission scheduled. Start it when the robot is ready.", "success");
      await loadMissions({ showLoading: false });
    } catch (error) {
      Fleet.notice(createNotice, error.message || "Could not create the mission.");
    } finally {
      submit.disabled = false;
      submit.textContent = "Create mission";
    }
  });

  loadOptions();
  loadMissions();
  window.setInterval(() => loadMissions({ showLoading: false }), 10000);
})();
