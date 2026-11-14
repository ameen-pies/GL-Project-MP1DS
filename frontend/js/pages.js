/* Module catalogue and honest queued states for later sprints. */

(() => {
  const MODULES = {
    robots: {
      num: "01",
      title: "Fleet registry",
      href: "/robots.html",
      cover: "periwinkle",
      label: "The registry",
      issue: "SCRUM-22 / 23",
      sprint: "Sprint 1",
      lede: "Register robots with a name and serial number, then search and scan the fleet at a glance.",
      body: "The registry will list name, serial number, status, and battery for every robot in your company. Admins get a registration form and a one-time API key screen. Operators get the read-only list.",
      unblocks: "Role-based login (SCRUM-20), so the registry can tell admins from operators.",
    },
    map: {
      num: "02",
      title: "Live map",
      href: "/map.html",
      cover: "ink",
      label: "The map",
      issue: "SCRUM-26",
      sprint: "Sprint 2",
      lede: "One marker per robot on OpenStreetMap, refreshed every five seconds.",
      body: "The live map will poll the latest telemetry for your company, draw a marker per robot, and open a popup with name and status. A side panel will mirror status and battery for the whole fleet.",
      unblocks: "Telemetry ingestion (SCRUM-24 and SCRUM-25), so there is a position to draw.",
    },
    missions: {
      num: "03",
      title: "Patrol missions",
      href: "/missions.html",
      cover: "outline",
      label: "The missions",
      issue: "SCRUM-28 / 29",
      sprint: "Sprint 3",
      lede: "Create a patrol from a seeded route, start it, and stop it.",
      body: "Missions will move through scheduled, running, stopped, and completed. Each transition is written to an event log with the operator and the time, and a robot can only run one mission at a time.",
      unblocks: "The mission data model (SCRUM-28) and the robot mission endpoint in SCRUM-29.",
    },
    alerts: {
      num: "04",
      title: "Alerts",
      href: "/alerts.html",
      cover: "deep",
      label: "The queue",
      issue: "SCRUM-30 / 31",
      sprint: "Sprint 3",
      lede: "Intrusion and obstacle events, queued for acknowledgement.",
      body: "Robot events will create alerts scoped to the company, email opted-in users in the background, and show an open count in the navigation. Acknowledging an alert records who handled it and when.",
      unblocks: "Telemetry auth (SCRUM-25) and the email service (SCRUM-30).",
    },
    analytics: {
      num: "05",
      title: "Analytics",
      href: "/analytics.html",
      cover: "ink",
      label: "The numbers",
      issue: "SCRUM-32 / 33",
      sprint: "Sprint 3 to 4",
      lede: "Weekly patrol coverage, battery history, and uptime.",
      body: "The analytics page will chart missions per day for the last seven days, with completed patrols in green and stopped patrols in red. The queries behind it are tested and indexed for a two-second budget.",
      unblocks: "The statistics queries (SCRUM-32) and the weekly endpoint in SCRUM-33.",
    },
    predictions: {
      num: "06",
      title: "Risk forecast",
      href: "/predictions.html",
      cover: "outline",
      label: "The forecast",
      issue: "SCRUM-35 to 37",
      sprint: "Sprint 4",
      lede: "High-risk hours, learned from incidents.",
      body: "An incident model will train on real alerts plus reproducible synthetic data, then surface the time slots where patrols are most likely to meet an intrusion or obstacle.",
      unblocks: "Alert history (SCRUM-31) and the incident dataset in SCRUM-35.",
    },
  };

  window.FleetModules = MODULES;

  function cardHTML(module) {
    return `
      <a class="fan__card" href="${module.href}">
        <span class="module-card">
          <span class="module-cover module-cover--${module.cover}">
            <span class="module-cover__num">${module.num}</span>
            <span class="module-cover__tag">${module.sprint}</span>
          </span>
          <span class="module-body">
            <span class="module-body__title">${module.title}</span>
            <span class="module-body__meta">${module.issue}</span>
          </span>
        </span>
      </a>`;
  }

  function modulePageHTML(module, key) {
    const keys = Object.keys(MODULES);
    const index = keys.indexOf(key);
    const prev = MODULES[keys[(index - 1 + keys.length) % keys.length]];
    const next = MODULES[keys[(index + 1) % keys.length]];
    return `
      <div class="page__inner">
        <article class="page-hero">
          <div class="page-hero__copy">
            <p class="eyebrow">
              Module ${module.num}
              <span class="eyebrow__sep">/</span>
              Queued
            </p>
            <h1 class="page-hero__title">${module.title}</h1>
            <p class="page-hero__lede">${module.lede}</p>
            <div class="page-hero__actions">
              <a class="btn btn--dark" href="/#modules">Back to modules</a>
              <a class="btn btn--outline" href="/">Overview</a>
            </div>
            <div class="page-hero__meta">
              <span class="chip chip--queued">${module.issue}</span>
              <span class="chip">${module.sprint}</span>
            </div>
          </div>
          <div class="page-cover page-cover--${module.cover}" aria-hidden="true">
            <span class="page-cover__num">${module.num}</span>
            <span class="page-cover__label">${module.label}</span>
            <span class="badge badge--dark">Queued</span>
          </div>
        </article>

        <section class="page-panel" aria-labelledby="panel-title">
          <div class="page-panel__main">
            <p class="eyebrow">In the build queue</p>
            <h2 id="panel-title">What this module will do</h2>
            <p>${module.body}</p>
            <div class="page-panel__next">
              <p class="eyebrow">Unblocks after</p>
              <p>${module.unblocks}</p>
            </div>
          </div>
          <aside class="page-panel__aside" aria-label="Module details">
            <p class="eyebrow">At a glance</p>
            <dl class="meta-list">
              <div>
                <dt>State</dt>
                <dd><span class="chip chip--queued">Queued</span></dd>
              </div>
              <div>
                <dt>Sprint</dt>
                <dd>${module.sprint}</dd>
              </div>
              <div>
                <dt>Issue</dt>
                <dd class="mono">${module.issue}</dd>
              </div>
              <div>
                <dt>Route</dt>
                <dd class="mono">${module.href}</dd>
              </div>
            </dl>
            <p class="page-panel__note">
              The route is live now; the data is not. This page will change when
              the module ships.
            </p>
          </aside>
        </section>

        <nav class="pager" aria-label="Module pages">
          <a class="pager__link" href="${prev.href}">
            <span class="pager__num" aria-hidden="true">${prev.num}</span>
            <span class="pager__label">
              <span>Previous</span>
              <span class="pager__title">${prev.title}</span>
            </span>
          </a>
          <a class="pager__link" href="${next.href}">
            <span class="pager__label">
              <span>Next</span>
              <span class="pager__title">${next.title}</span>
            </span>
            <span class="pager__num" aria-hidden="true">${next.num}</span>
          </a>
        </nav>
      </div>`;
  }

  const pageKey = document.body.dataset.page;
  const main = document.getElementById("main");
  if (!main) return;

  if (pageKey === "overview") {
    const fan = document.getElementById("module-fan");
    if (fan) {
      fan.innerHTML = Object.values(MODULES)
        .map((module) => cardHTML(module))
        .join("");
    }
    return;
  }

  const module = MODULES[pageKey];
  if (!module) return;

  document.title = `${module.title} \u00b7 Fleet Control`;
  main.innerHTML = modulePageHTML(module, pageKey);
})();
