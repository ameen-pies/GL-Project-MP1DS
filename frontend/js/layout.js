/* Shared shell: auth state, navigation, alert badge, UTC clock, footer. */

(() => {
  const NAV_ITEMS = [
    { href: "/", label: "Overview", page: "overview" },
    { href: "/robots.html", label: "Fleet", page: "robots" },
    { href: "/map.html", label: "Live map", page: "map" },
    { href: "/missions.html", label: "Missions", page: "missions" },
    { href: "/alerts.html", label: "Alerts", page: "alerts", alertBadge: true },
    { href: "/analytics.html", label: "Analytics", page: "analytics" },
    { href: "/predictions.html", label: "Risk", page: "predictions" },
  ];

  const Fleet = window.Fleet;
  if (!Fleet) return;

  const currentPage = document.body.dataset.page;
  const requiresAuth = document.body.dataset.auth === "required";
  const minimal = document.body.dataset.shell === "minimal";
  const session = Fleet.user();

  if (requiresAuth && !Fleet.token()) {
    window.location.replace(
      `/login.html?next=${encodeURIComponent(window.location.pathname)}`,
    );
    return;
  }

  function isActive(page) {
    return currentPage === page;
  }

  function brandHTML() {
    return `<a class="brand" href="/"><span class="brand__mark" aria-hidden="true"></span>Fleet Control</a>`;
  }

  function clockHTML() {
    return `<span class="header__clock">
      <span>UTC</span>
      <span data-clock>--:--:--</span>
    </span>`;
  }

  function navItems() {
    const items = [...NAV_ITEMS];
    if (session && session.role === "admin") {
      items.push({ href: "/robot-new.html", label: "Register", page: "robot-new" });
    }
    return items;
  }

  function headerHTML() {
    if (minimal) {
      return `
        <div class="header__inner">
          ${brandHTML()}
          <div class="header__meta">${clockHTML()}</div>
        </div>`;
    }

    const links = navItems()
      .map((item) => {
        const current = isActive(item.page) ? ' aria-current="page"' : "";
        const badge = item.alertBadge
          ? ` <span class="nav__badge" data-alert-count hidden>0</span>`
          : "";
        return `<a class="nav__link" href="${item.href}"${current}>${item.label}${badge}</a>`;
      })
      .join("");

    const account = session
      ? `<span class="header__user">
           <span class="header__user-name">${Fleet.escapeHtml(session.full_name)}</span>
           <span class="header__user-role">${Fleet.escapeHtml(session.role)}</span>
         </span>
         <button class="btn btn--ghost btn--sm" type="button" data-logout>Log out</button>`
      : `<a class="btn btn--dark btn--sm" href="/login.html">Log in</a>`;

    return `
      <div class="header__inner">
        ${brandHTML()}
        <nav class="nav" aria-label="Primary">${links}</nav>
        <div class="header__meta">
          ${account}
          ${clockHTML()}
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
            <li>All four sprints shipped</li>
            <li>UTC storage · local display</li>
          </ul>
          <p class="footer__status" data-health>
            <span class="status-dot status-dot--off" aria-hidden="true"></span>
            Checking API
          </p>
        </div>
      </div>
      <div class="footer__bottom">
        <p>Fleet Control · Practice build</p>
        <p><span data-clock>--:--:--</span> UTC</p>
        <a class="footer__top" href="#main">Back to top <span aria-hidden="true">↑</span></a>
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

  async function checkHealth() {
    const targets = [...document.querySelectorAll("[data-health]")];
    if (!targets.length) return;

    let healthy = false;
    try {
      const body = await Fleet.api("/api/v1/health");
      healthy = body.status === "ok" && body.database === "up";
    } catch {
      healthy = false;
    }

    targets.forEach((target) => {
      target.innerHTML = `<span class="status-dot ${healthy ? "status-dot--live" : "status-dot--off"}" aria-hidden="true"></span>${
        healthy ? "API up · database reachable" : "API unreachable"
      }`;
    });
  }

  async function refreshAlertCount() {
    const badges = [...document.querySelectorAll("[data-alert-count]")];
    if (!badges.length || !Fleet.token()) return;
    try {
      const { count } = await Fleet.api("/api/v1/alerts/open-count");
      badges.forEach((badge) => {
        badge.hidden = count === 0;
        badge.textContent = count > 99 ? "99+" : String(count);
      });
    } catch {
      /* The badge is decoration; keep the shell usable when polling fails. */
    }
  }

  const header = document.getElementById("site-header");
  if (header) header.innerHTML = headerHTML();

  const footer = document.getElementById("site-footer");
  if (footer) {
    footer.hidden = minimal;
    footer.innerHTML = minimal ? "" : footerHTML();
  }

  document.querySelectorAll("[data-logout]").forEach((button) => {
    button.addEventListener("click", () => Fleet.logout());
  });

  startClock();
  if (!minimal) checkHealth();

  if (session && !minimal) {
    refreshAlertCount();
    window.setInterval(refreshAlertCount, 10000);
  }
})();
