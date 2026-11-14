/* Overview: the six module cards, now pointing at the shipped routes. */

(() => {
  const MODULES = {
    robots: {
      num: "01",
      title: "Fleet registry",
      href: "/robots.html",
      cover: "periwinkle",
      issue: "SCRUM-20 / 22 / 23",
      sprint: "Sprint 1",
      lede: "Role-based login, robot registration, search, status, and battery.",
    },
    map: {
      num: "02",
      title: "Live map",
      href: "/map.html",
      cover: "ink",
      issue: "SCRUM-24 to 27",
      sprint: "Sprint 2",
      lede: "Telemetry ingestion, OpenStreetMap markers, status panel, 5-second polling.",
    },
    missions: {
      num: "03",
      title: "Patrol missions",
      href: "/missions.html",
      cover: "outline",
      issue: "SCRUM-28 / 29",
      sprint: "Sprint 3",
      lede: "Create from a seeded route, start and stop remotely, read the event log.",
    },
    alerts: {
      num: "04",
      title: "Alerts",
      href: "/alerts.html",
      cover: "deep",
      issue: "SCRUM-30 / 31",
      sprint: "Sprint 3",
      lede: "Intrusion and obstacle alerts, email notifications, acknowledgement.",
    },
    analytics: {
      num: "05",
      title: "Analytics",
      href: "/analytics.html",
      cover: "ink",
      issue: "SCRUM-32 / 33",
      sprint: "Sprint 3 to 4",
      lede: "Weekly patrol coverage, completed versus stopped, week by week.",
    },
    predictions: {
      num: "06",
      title: "Risk forecast",
      href: "/predictions.html",
      cover: "outline",
      issue: "SCRUM-35 to 37",
      sprint: "Sprint 4",
      lede: "Hourly incident risk for the next 24 hours, from a trained model.",
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

  const fan = document.getElementById("module-fan");
  if (fan) {
    fan.innerHTML = Object.values(MODULES).map(cardHTML).join("");
  }
})();
