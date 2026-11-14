/* Shared shell: header navigation, UTC clocks, and footer. */

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

  function isActive(page) {
    return document.body.dataset.page === page;
  }

  function brandHTML() {
    return `<a class="brand" href="/"><span class="brand__mark" aria-hidden="true"></span>Fleet Control</a>`;
  }

  function headerHTML() {
    const links = NAV_ITEMS.map((item) => {
      const current = isActive(item.page) ? ' aria-current="page"' : "";
      return `<a class="nav__link" href="${item.href}"${current}>${item.label}</a>`;
    }).join("");

    return `
      <div class="header__inner">
        ${brandHTML()}
        <nav class="nav" aria-label="Primary">${links}</nav>
        <div class="header__meta">
          <span class="header__clock">
            <span>UTC</span>
            <span data-clock>--:--:--</span>
          </span>
        </div>
      </div>`;
  }

  function footerHTML() {
    return `
      <div class="footer__inner">
        <div class="footer__brand">
          ${brandHTML()}
          <p>
            A supervision desk for security patrol robots. Built as a practice
            project, one sprint at a time.
          </p>
        </div>
        <nav class="footer__col" aria-label="Sections">
          <h3>Sections</h3>
          <ul>
            <li><a href="/">Overview</a></li>
            <li><a href="/robots.html">Fleet registry</a></li>
            <li><a href="/map.html">Live map</a></li>
            <li><a href="/missions.html">Patrol missions</a></li>
          </ul>
        </nav>
        <nav class="footer__col" aria-label="More">
          <h3>More</h3>
          <ul>
            <li><a href="/alerts.html">Alerts</a></li>
            <li><a href="/analytics.html">Analytics</a></li>
            <li><a href="/predictions.html">Risk forecast</a></li>
            <li><a href="/#modules">Module map</a></li>
          </ul>
        </nav>
        <div class="footer__col">
          <h3>Build</h3>
          <ul>
            <li>FastAPI + SQLite</li>
            <li>Shell 0.1</li>
            <li>6 modules queued</li>
          </ul>
          <p class="footer__status">
            <span class="status-dot status-dot--off" aria-hidden="true"></span>
            No telemetry connected
          </p>
        </div>
      </div>
      <div class="footer__bottom">
        <p>Fleet Control \u00b7 Practice build</p>
        <p><span data-clock>--:--:--</span> UTC</p>
        <a class="footer__top" href="#main">Back to top <span aria-hidden="true">\u2191</span></a>
      </div>`;
  }

  function startClock() {
    const targets = [...document.querySelectorAll("[data-clock]")];
    if (!targets.length) return;

    const formatter = new Intl.DateTimeFormat("en-GB", {
      timeZone: "UTC",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });

    const tick = () => {
      const time = formatter.format(new Date());
      targets.forEach((target) => {
        target.textContent = time;
      });
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
