/* Live map: one marker per robot, refreshed every 5 seconds, with a status panel. */

(() => {
  const Fleet = window.Fleet;
  const main = document.getElementById("main");
  if (!Fleet || !main) return;

  main.innerHTML = `
    <div class="app">
      <header class="app-head">
        <div class="app-head__copy">
          <p class="eyebrow">Module 02 <span class="eyebrow__sep">/</span> Live picture</p>
          <h1 class="app-title">Live map</h1>
          <p class="app-lede">
            Positions refresh every five seconds. A unit without a sample in the
            last minute reads offline rather than showing stale coordinates.
          </p>
        </div>
        <div class="app-actions">
          <a class="btn btn--ghost" href="/robots.html">Fleet registry</a>
          <a class="btn btn--outline" href="/missions.html">Missions</a>
        </div>
      </header>

      <div class="map-layout">
        <section class="map-shell" aria-label="Robot positions map">
          <div class="map-note" id="map-note" hidden></div>
          <div id="map"></div>
          <div class="map-shell__foot">
            <p>Polling every 5 s · OpenStreetMap</p>
            <p id="map-updated">Waiting for the first sample</p>
          </div>
        </section>

        <aside class="map-panel" aria-labelledby="panel-title">
          <div class="map-panel__head">
            <h2 class="map-panel__title" id="panel-title">Status panel</h2>
            <span class="app-note" id="panel-count"></span>
          </div>
          <div class="map-panel__body" id="panel-body">
            <p class="state" role="status">Loading robots…</p>
          </div>
        </aside>
      </div>
    </div>`;

  const note = document.getElementById("map-note");
  const panel = document.getElementById("panel-body");
  const panelCount = document.getElementById("panel-count");
  const updated = document.getElementById("map-updated");

  if (!window.L) {
    Fleet.errorState(panel, "The map library could not load. Check the network and reload.");
    note.hidden = false;
    note.textContent = "Map unavailable";
    note.classList.add("map-note--error");
    return;
  }

  const map = L.map("map", {
    center: [35.8256, 10.6369],
    zoom: 15,
    zoomControl: true,
    scrollWheelZoom: true,
  });

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  const markers = new Map();
  let fitted = false;
  let selectedId = null;

  function icon(status) {
    const modifier =
      status === "active" ? "" : status === "idle" ? " map-marker--idle" : " map-marker--offline";
    return L.divIcon({
      className: "map-marker-wrap",
      html: `<span class="map-marker${modifier}"></span>`,
      iconSize: [22, 22],
      iconAnchor: [11, 11],
      popupAnchor: [0, -12],
    });
  }

  function popupHTML(robot) {
    return `
      <strong>${Fleet.escapeHtml(robot.name)}</strong><br />
      ${Fleet.statusChip(robot.status)}
      <div class="mono">${Fleet.escapeHtml(robot.serial_number)}</div>`;
  }

  function panelHTML(robots) {
    return robots
      .map(
        (robot) => `
        <button class="robot-row" type="button" data-robot="${robot.id}" aria-pressed="${
          String(selectedId === robot.id)
        }">
          <span class="robot-row__top">
            <span class="robot-row__name">${Fleet.escapeHtml(robot.name)}</span>
            ${Fleet.statusChip(robot.status)}
          </span>
          <span class="robot-row__meta">
            <span>${Fleet.escapeHtml(robot.serial_number)}</span>
            ${Fleet.batteryBadge(robot.battery_pct, robot.status)}
          </span>
        </button>`,
      )
      .join("");
  }

  function draw(robots) {
    panelCount.textContent = `${robots.length} unit${robots.length === 1 ? "" : "s"}`;

    if (!robots.length) {
      Fleet.empty(panel, "No robots yet. An admin can register the first unit.");
      note.hidden = false;
      note.textContent = "No robots registered for this company.";
      note.classList.remove("map-note--error");
      updated.textContent = "No telemetry";
      return;
    }

    panel.innerHTML = panelHTML(robots);
    panel.querySelectorAll("[data-robot]").forEach((row) => {
      row.addEventListener("click", () => focusRobot(Number(row.dataset.robot)));
    });

    const placed = robots.filter((robot) => robot.lat !== null && robot.lng !== null);
    const latest = placed.reduce((newest, robot) => {
      if (!newest || new Date(robot.last_seen) > new Date(newest)) return robot.last_seen;
      return newest;
    }, null);
    updated.textContent = latest ? `Last sample ${Fleet.relative(latest)}` : "No telemetry yet";

    if (!placed.length) {
      note.hidden = false;
      note.textContent = "No robot has sent a position yet. Start the simulator to see them move.";
      note.classList.remove("map-note--error");
      return;
    }

    note.hidden = true;

    const seen = new Set();
    placed.forEach((robot) => {
      seen.add(robot.id);
      const position = [robot.lat, robot.lng];
      let entry = markers.get(robot.id);
      if (!entry) {
        const marker = L.marker(position, { icon: icon(robot.status) }).addTo(map);
        marker.bindPopup(popupHTML(robot));
        entry = { marker };
        markers.set(robot.id, entry);
      } else {
        entry.marker.setLatLng(position);
        entry.marker.setIcon(icon(robot.status));
        entry.marker.setPopupContent(popupHTML(robot));
      }
    });

    for (const [id, entry] of markers) {
      if (!seen.has(id)) {
        entry.marker.remove();
        markers.delete(id);
      }
    }

    if (!fitted) {
      const bounds = L.latLngBounds(placed.map((robot) => [robot.lat, robot.lng]));
      map.fitBounds(bounds.pad(0.35), { maxZoom: 17 });
      fitted = true;
    }
  }

  function focusRobot(id) {
    selectedId = id;
    panel.querySelectorAll("[data-robot]").forEach((row) => {
      row.setAttribute("aria-pressed", String(Number(row.dataset.robot) === id));
    });
    const entry = markers.get(id);
    if (entry) {
      map.setView(entry.marker.getLatLng(), Math.max(map.getZoom(), 17), { animate: true });
      entry.marker.openPopup();
    }
  }

  async function load() {
    try {
      const robots = await Fleet.api("/api/v1/robots/latest");
      draw(robots);
    } catch (error) {
      note.hidden = false;
      note.textContent = error.message || "Could not load positions.";
      note.classList.add("map-note--error");
      if (!panel.querySelector(".robot-row")) {
        Fleet.errorState(panel, error.message || "Could not load the fleet.");
      }
    }
  }

  load();
  window.setInterval(load, 5000);
})();
