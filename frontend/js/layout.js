/* Shared application shell: brand, primary navigation, UTC clock, footer. */

(() => {
  const NAV_ITEMS = [
    { href: "/robots.html", label: "Fleet", page: "robots" },
    { href: "/map.html", label: "Live map", page: "map" },
    { href: "/missions.html", label: "Missions", page: "missions" },
    { href: "/alerts.html", label: "Alerts", page: "alerts" },
    { href: "/analytics.html", label: "Analytics", page: "analytics" },
    { href: "/predictions.html", label: "Risk", page: "predictions" },
  ];

  const BRAND_MARK = `
    <svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <rect x="1" y="1" width="30" height="30" rx="7" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.45" />
      <path d="M8.5 23.5a11 11 0 0 1 11-11" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
      <path d="M12.5 23.5a7 7 0 0 1 7-7" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" opacity="0.6" />
      <circle cx="23.5" cy="23.5" r="2.1" fill="currentColor" />
    </svg>`;

  function isActive(page) {
    return document.body.dataset.page === page;
  }

  function headerHTML() {
    const links = NAV_ITEMS.map((item) => {
      const current = isActive(item.page) ? ' aria-current="page"' : "";
      return `<a class="nav__link" href="${item.href}"${current}>${item.label}</a>`;
    }).join("");

    return `
      <div class="topbar">
        <div class="topbar__inner">
          <a class="brand" href="/" aria-label="Fleet Control home">
            <span class="brand__mark">${BRAND_MARK}</span>
            <span class="brand__text">
              <span class="brand__name">Fleet Control</span>
              <span class="brand__tag">Patrol operations</span>
            </span>
          </a>
          <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav" aria-label="Open navigation">
            <span class="nav-toggle__bar"></span>
            <span class="nav-toggle__bar"></span>
            <span class="nav-toggle__bar"></span>
          </button>
          <nav class="nav" id="primary-nav" aria-label="Primary">
            ${links}
          </nav>
          <div class="topbar__meta">
            <span class="clock mono" title="Coordinated Universal Time">
              <span class="clock__label">UTC</span>
              <span data-clock>--:--:--</span>
            </span>
            <span class="preview-chip">Shell build</span>
          </div>
        </div>
      </div>`;
  }

  function footerHTML() {
    return `
      <div class="footer__inner">
        <p>Fleet Control <span class="footer__sep">/</span> Practice build <span class="footer__sep">/</span> FastAPI + SQLite</p>
        <p class="mono">No telemetry connected</p>
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

  function initNav() {
    const toggle = document.querySelector(".nav-toggle");
    const nav = document.getElementById("primary-nav");
    if (!toggle || !nav) return;

    const close = () => {
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Open navigation");
    };

    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
    });

    nav.addEventListener("click", (event) => {
      if (event.target.closest("a") && window.matchMedia("(max-width: 980px)").matches) {
        close();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") close();
    });
  }

  const header = document.getElementById("site-header");
  if (header) header.innerHTML = headerHTML();

  const footer = document.getElementById("site-footer");
  if (footer) footer.innerHTML = footerHTML();

  initNav();
  startClock();
})();
