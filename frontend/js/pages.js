/* Honest empty states for modules that land in later sprints. */

(() => {
  const PAGES = {
    robots: {
      title: "Fleet registry",
      eyebrow: "Module",
      icon: "robot",
      issue: "SCRUM-22 / 23",
      sprint: "Sprint 1",
      lede: "Register robots with a name and serial number, then search and scan the fleet at a glance.",
      body: "The registry will list name, serial number, status, and battery for every robot in your company. Admins get a registration form and a one-time API key screen. Operators get the read-only list.",
      unblocks: "Role-based login (SCRUM-20), so the registry can tell admins from operators.",
    },
    map: {
      title: "Live map",
      eyebrow: "Module",
      icon: "pin",
      issue: "SCRUM-26",
      sprint: "Sprint 2",
      lede: "One marker per robot on OpenStreetMap, refreshed every five seconds.",
      body: "The live map will poll the latest telemetry for your company, draw a marker per robot, and open a popup with name and status. A side panel will mirror status and battery for the whole fleet.",
      unblocks: "Telemetry ingestion (SCRUM-24 and SCRUM-25), so there is a position to draw.",
    },
    missions: {
      title: "Patrol missions",
      eyebrow: "Module",
      icon: "flag",
      issue: "SCRUM-28 / 29",
      sprint: "Sprint 3",
      lede: "Create a patrol from a seeded route, start it, and stop it.",
      body: "Missions will move through scheduled, running, stopped, and completed. Each transition is written to an event log with the operator and the time, and a robot can only run one mission at a time.",
      unblocks: "The mission data model (SCRUM-28) and the robot mission endpoint in SCRUM-29.",
    },
    alerts: {
      title: "Alerts",
      eyebrow: "Module",
      icon: "bell",
      issue: "SCRUM-30 / 31",
      sprint: "Sprint 3",
      lede: "Intrusion and obstacle events, queued for acknowledgement.",
      body: "Robot events will create alerts scoped to the company, email opted-in users in the background, and show an open count in the navigation. Acknowledging an alert records who handled it and when.",
      unblocks: "Telemetry auth (SCRUM-25) and the email service (SCRUM-30).",
    },
    analytics: {
      title: "Analytics",
      eyebrow: "Module",
      icon: "chart",
      issue: "SCRUM-32 / 33",
      sprint: "Sprint 3 to 4",
      lede: "Weekly patrol coverage, battery history, and uptime.",
      body: "The analytics page will chart missions per day for the last seven days, with completed patrols in green and stopped patrols in red. The queries behind it are tested and indexed for a two-second budget.",
      unblocks: "The statistics queries (SCRUM-32) and the weekly endpoint in SCRUM-33.",
    },
    predictions: {
      title: "Risk forecast",
      eyebrow: "Module",
      icon: "bolt",
      issue: "SCRUM-35 to 37",
      sprint: "Sprint 4",
      lede: "High-risk hours, learned from incidents.",
      body: "An incident model will train on real alerts plus reproducible synthetic data, then surface the time slots where patrols are most likely to meet an intrusion or obstacle.",
      unblocks: "Alert history (SCRUM-31) and the incident dataset in SCRUM-35.",
    },
  };

  const page = PAGES[document.body.dataset.page];
  const main = document.getElementById("main");
  if (!page || !main) return;

  document.title = `${page.title} \u00b7 Fleet Control`;

  const icon = window.FleetIcons ? window.FleetIcons.svg(page.icon) : "";

  main.innerHTML = `
    <section class="page-head">
      <p class="eyebrow">${page.eyebrow} <span class="eyebrow__sep">/</span> Queued</p>
      <div class="page-head__row">
        <div>
          <h1 class="page-title">${page.title}</h1>
          <p class="page-lede">${page.lede}</p>
        </div>
        <div class="page-head__actions">
          <span class="chip chip--queued">${page.issue}</span>
          <span class="module-card__sprint">${page.sprint}</span>
        </div>
      </div>
    </section>

    <section class="module-card" aria-labelledby="module-title">
      <div class="module-card__aside">
        <div class="module-icon">${icon}</div>
        <div class="module-card__flag">
          <span class="chip chip--queued">Queued</span>
        </div>
      </div>
      <div class="module-card__body">
        <h2 id="module-title">In the build queue</h2>
        <p>${page.body}</p>
        <div class="module-card__next">
          <p class="eyebrow">Unblocks after</p>
          <p>${page.unblocks}</p>
        </div>
        <div class="module-card__actions">
          <a class="btn btn--ghost" href="/">Back to overview</a>
          <a class="btn btn--accent" href="/#modules">Module map</a>
        </div>
      </div>
    </section>`;
})();
