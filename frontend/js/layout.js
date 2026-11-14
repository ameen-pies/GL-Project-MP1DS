/* Shared application shell: window chrome, masthead, capsule nav, clock, footer. */

(() => {
  const NAV_ITEMS = [
    { href: "/", label: "Overview", page: "overview" },
    { href: "/robots.html", label: "Fleet", page: "robots" },
    { href: "/map.html", label: "Live map", page: "map" },
    { href: "/missions.html", label: "Missions", page: "missions" },
    { href: "/alerts.html", label: "Alerts", page: "alerts" },
    { href: "/analytics.html", label: "Analytics", page: "analytics" },
    { href: "/predictions.html", label: "Risk", page: "predictions" },
  ];

  /* 12 x 12 pixel maps. # = ink, y = yellow, w = paper, . = empty. */
  const ICONS = {
    robot: [
      "............",
      "...#....#...",
      "...#....#...",
      "..########..",
      ".##########.",
      ".###ww##ww#.",
      ".###yyyy###.",
      "..########..",
      ".##########.",
      ".###.yy.###.",
      ".##########.",
      "..##....##..",
    ],
    pin: [
      "............",
      "....####....",
      "..########..",
      ".##########.",
      ".###wwww###.",
      ".###wwww###.",
      ".##########.",
      "..########..",
      "...######...",
      "....####....",
      ".....##.....",
      "............",
    ],
    flag: [
      "............",
      "..#.........",
      "..#yyyyyy...",
      "..#yyyyyyy..",
      "..#yyyyyy...",
      "..#.........",
      "..#.........",
      "..#.........",
      "..#.........",
      "..#.........",
      "..#.........",
      ".#####......",
    ],
    bell: [
      ".....##.....",
      "....####....",
      "...######...",
      "...######...",
      "..########..",
      "..########..",
      ".##########.",
      ".##########.",
      "############",
      "............",
      ".....##.....",
      "............",
    ],
    chart: [
      "............",
      "............",
      ".....yy.....",
      ".....yy.....",
      ".....yy.....",
      ".##..yy.....",
      ".##..yy.....",
      ".##..yy..##.",
      ".##..yy..##.",
      ".##..yy..##.",
      "############",
      "............",
    ],
    bolt: [
      "....###.....",
      "...###......",
      "..###.......",
      ".###........",
      "########....",
      "....###.....",
      "...###......",
      "..###.......",
      ".###........",
      "###.........",
      "............",
      "............",
    ],
    star: [
      ".....##.....",
      ".....##.....",
      "....####....",
      "..########..",
      "############",
      ".##########.",
      "..########..",
      "..########..",
      "..###..###..",
      ".###....###.",
      ".##......##.",
      "............",
    ],
    battery: [
      "............",
      "............",
      "#########...",
      "#yyyyyyy#...",
      "#yyyyyyy#...",
      "#yyyyyyy#.##",
      "#yyyyyyy#.##",
      "#yyyyyyy#...",
      "#########...",
      "............",
      "............",
      "............",
    ],
    floppy: [
      "############",
      "#wwwww##www#",
      "#wwwww##www#",
      "#wwwww##www#",
      "############",
      "#wwwwwwwwww#",
      "#wwwwwwwwww#",
      "#wwwwwwwwww#",
      "#wwwwwwwwww#",
      "#wwwwwwwwww#",
      "#wwwwwwwwww#",
      "############",
    ],
  };

  function iconSVG(name, className = "pixel-icon") {
    const rows = ICONS[name] || ICONS.robot;
    const rects = [];

    rows.forEach((row, y) => {
      [...row].forEach((cell, x) => {
        if (cell === ".") return;
        const fill = cell === "y" ? "var(--yellow)" : cell === "w" ? "#ffffff" : "currentColor";
        rects.push(`<rect x="${x}" y="${y}" width="1" height="1" fill="${fill}" />`);
      });
    });

    return `<svg class="${className}" viewBox="0 0 12 12" aria-hidden="true" focusable="false" shape-rendering="crispEdges">${rects.join("")}</svg>`;
  }

  window.FleetIcons = { svg: iconSVG };

  function isActive(page) {
    return document.body.dataset.page === page;
  }

  function headerHTML() {
    const links = NAV_ITEMS.map((item) => {
      const current = isActive(item.page) ? ' aria-current="page"' : "";
      return `<a class="nav__link" href="${item.href}"${current}>${item.label}</a>`;
    }).join("");

    const date = new Intl.DateTimeFormat("en-GB", {
      timeZone: "UTC",
      weekday: "short",
      day: "2-digit",
      month: "short",
      year: "numeric",
    })
      .format(new Date())
      .replace(/,/g, "")
      .toUpperCase();

    return `
      <div class="topbar">
        <span class="topbar__label">
          <span class="topbar__date">${date}</span>
          <span class="topbar__sep" aria-hidden="true">/</span>
          <span class="topbar__section">Patrol operations console</span>
        </span>
        <div class="topbar__meta">
          <span class="window-clock mono">
            <span class="window-clock__label">UTC</span>
            <span data-clock>--:--:--</span>
          </span>
          <span class="window-badge">Shell 0.1</span>
        </div>
      </div>
      <header class="masthead">
        <div class="masthead__icons" aria-hidden="true">
          ${iconSVG("robot", "masthead__icon masthead__icon--robot")}
          ${iconSVG("battery", "masthead__icon masthead__icon--battery")}
          ${iconSVG("pin", "masthead__icon masthead__icon--pin")}
          ${iconSVG("floppy", "masthead__icon masthead__icon--floppy")}
          ${iconSVG("star", "masthead__icon masthead__icon--star")}
        </div>
        <a class="wordmark" href="/" aria-label="Fleet Control home">Fleet Control</a>
        <p class="masthead__sub">
          Patrol robot supervision
          <span class="masthead__dot">\u00b7</span>
          Practice build
        </p>
        <nav class="nav" aria-label="Primary">${links}</nav>
      </header>`;
  }

  function footerHTML() {
    return `
      <div class="footer__inner">
        <p>
          Fleet Control
          <span class="footer__sep">/</span>
          Practice build
          <span class="footer__sep">/</span>
          FastAPI + SQLite
        </p>
        <p class="footer__status">
          <span class="status-dot status-dot--off" aria-hidden="true"></span>
          No telemetry connected
        </p>
      </div>`;
  }

  function startClock() {
    const target = document.querySelector("[data-clock]");
    if (!target) return;

    const formatter = new Intl.DateTimeFormat("en-GB", {
      timeZone: "UTC",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });

    const tick = () => {
      target.textContent = formatter.format(new Date());
    };

    tick();
    window.setInterval(tick, 1000);
  }

  const header = document.getElementById("site-header");
  if (header) header.innerHTML = headerHTML();

  const footer = document.getElementById("site-footer");
  if (footer) footer.innerHTML = footerHTML();

  startClock();
})();
