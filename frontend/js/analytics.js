/* Weekly patrol summary: stacked bars, completed in green, stopped in red. */

(() => {
  const Fleet = window.Fleet;
  const main = document.getElementById("main");
  if (!Fleet || !main) return;

  main.innerHTML = `
    <div class="app">
      <header class="app-head">
        <div class="app-head__copy">
          <p class="eyebrow">Module 05 <span class="eyebrow__sep">/</span> Coverage</p>
          <h1 class="app-title">Weekly patrols</h1>
          <p class="app-lede">
            Missions per day by final state. The chart always shows seven days,
            including days with no patrol at all.
          </p>
        </div>
        <div class="app-actions">
          <a class="btn btn--ghost" href="/missions.html">Mission queue</a>
        </div>
      </header>

      <div class="analytics-layout">
        <section class="chart-card" aria-labelledby="chart-title">
          <div class="chart-head">
            <div>
              <h2 class="panel__title" id="chart-title">Missions per day</h2>
              <p class="chart-head__range" id="range">Loading…</p>
            </div>
            <div class="chart-head__controls">
              <button class="btn btn--ghost btn--sm" type="button" id="prev">← Previous week</button>
              <button class="btn btn--ghost btn--sm" type="button" id="next">Next week →</button>
            </div>
          </div>
          <div id="chart" aria-live="polite">
            <p class="state" role="status">Loading the week…</p>
          </div>
          <div class="legend">
            <span class="legend__item"><span class="legend__swatch legend__swatch--completed"></span>Completed</span>
            <span class="legend__item"><span class="legend__swatch legend__swatch--stopped"></span>Stopped</span>
          </div>
        </section>

        <aside class="panel panel--aside" aria-labelledby="breakdown-title">
          <div class="panel__head">
            <h2 class="panel__title" id="breakdown-title">At a glance</h2>
          </div>
          <div class="metrics" id="metrics"></div>
          <div class="week-list" id="breakdown" style="margin-top: 1rem"></div>
        </aside>
      </div>
    </div>`;

  const chart = document.getElementById("chart");
  const range = document.getElementById("range");
  const metrics = document.getElementById("metrics");
  const breakdown = document.getElementById("breakdown");
  const prev = document.getElementById("prev");
  const next = document.getElementById("next");

  let weekOffset = 0;

  const dayLabel = (iso) =>
    new Intl.DateTimeFormat("en-GB", {
      day: "2-digit",
      month: "short",
      timeZone: "UTC",
    }).format(new Date(`${iso}T00:00:00Z`));

  function niceMax(value) {
    if (value <= 4) return 4;
    return Math.ceil(value / 4) * 4;
  }

  function chartHTML(days) {
    const width = 720;
    const height = 320;
    const pad = { top: 18, right: 12, bottom: 36, left: 34 };
    const plotWidth = width - pad.left - pad.right;
    const plotHeight = height - pad.top - pad.bottom;
    const totals = days.map((day) => day.completed + day.stopped);
    const max = niceMax(Math.max(1, ...totals));
    const band = plotWidth / days.length;
    const barWidth = Math.min(46, band * 0.56);

    const grid = [0, 0.25, 0.5, 0.75, 1]
      .map((ratio) => {
        const y = pad.top + plotHeight - plotHeight * ratio;
        const value = Math.round(max * ratio);
        return `
          <line x1="${pad.left}" y1="${y}" x2="${width - pad.right}" y2="${y}" />
          <text x="${pad.left - 8}" y="${y + 3}" text-anchor="end">${value}</text>`;
      })
      .join("");

    const bars = days
      .map((day, index) => {
        const x = pad.left + band * index + (band - barWidth) / 2;
        const baseline = pad.top + plotHeight;
        const scale = plotHeight / max;
        const completedHeight = day.completed * scale;
        const stoppedHeight = day.stopped * scale;
        const completedY = baseline - completedHeight;
        const stoppedY = completedY - stoppedHeight;
        const label = `${dayLabel(day.date)}: ${day.completed} completed, ${day.stopped} stopped`;
        return `
          <g class="chart-bar" tabindex="0" role="graphics-symbol" aria-label="${label}">
            <title>${label}</title>
            ${
              day.completed
                ? `<rect class="chart-bar--completed" x="${x}" y="${completedY}" width="${barWidth}" height="${completedHeight}" rx="2" />`
                : ""
            }
            ${
              day.stopped
                ? `<rect class="chart-bar--stopped" x="${x}" y="${stoppedY}" width="${barWidth}" height="${stoppedHeight}" rx="2" />`
                : ""
            }
            ${
              totals[index] === 0
                ? `<rect x="${x}" y="${baseline - 1}" width="${barWidth}" height="1" fill="var(--line-strong)" />`
                : ""
            }
            <text class="chart-label" x="${x + barWidth / 2}" y="${baseline + 20}" text-anchor="middle">${dayLabel(day.date)}</text>
          </g>`;
      })
      .join("");

    const totalMissions = totals.reduce((sum, value) => sum + value, 0);
    return `
      <svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img"
           aria-label="Stacked bar chart of completed and stopped missions per day. ${
             totalMissions === 0 ? "No missions this week." : `${totalMissions} missions this week.`
           }">
        <g class="chart-grid">${grid}</g>
        <g class="chart-axis">${bars}</g>
      </svg>`;
  }

  function render(data) {
    const days = data.days || [];
    const from = data.from;
    const to = data.to;
    range.textContent = `${dayLabel(from)} → ${dayLabel(to)} · week ${weekOffset === 0 ? "current" : `−${weekOffset}`}`;

    const totals = days.reduce(
      (acc, day) => {
        acc.completed += day.completed;
        acc.stopped += day.stopped;
        return acc;
      },
      { completed: 0, stopped: 0 },
    );
    const total = totals.completed + totals.stopped;

    chart.innerHTML = `
      ${total === 0 ? `<p class="notice notice--info">No missions this week. The seven days are still shown.</p>` : ""}
      ${chartHTML(days)}`;

    metrics.innerHTML = `
      <div class="metric">
        <span class="metric__label">Missions</span>
        <span class="metric__value">${total}</span>
      </div>
      <div class="metric">
        <span class="metric__label">Completed</span>
        <span class="metric__value">${totals.completed}</span>
      </div>
      <div class="metric">
        <span class="metric__label">Stopped</span>
        <span class="metric__value">${totals.stopped}</span>
      </div>
      <div class="metric">
        <span class="metric__label">Completion</span>
        <span class="metric__value">${total ? Math.round((totals.completed / total) * 100) : 0}<small>%</small></span>
      </div>`;

    breakdown.innerHTML = days
      .map(
        (day) => `
        <div class="week-list__row">
          <span class="week-list__date">${dayLabel(day.date)}</span>
          <span class="week-list__values">
            <span class="is-live"><strong>${day.completed}</strong> done</span>
            <span class="is-stop"><strong>${day.stopped}</strong> stopped</span>
          </span>
        </div>`,
      )
      .join("");

    prev.disabled = weekOffset >= 52;
    next.disabled = weekOffset <= 0;
  }

  async function load() {
    Fleet.loading(chart, "Loading the week…");
    try {
      const data = await Fleet.api(
        `/api/v1/analytics/missions/weekly?week_offset=${weekOffset}`,
      );
      render(data);
    } catch (error) {
      Fleet.errorState(chart, error.message || "Could not load the weekly summary.");
      range.textContent = "Unavailable";
      metrics.innerHTML = "";
      breakdown.innerHTML = "";
    }
  }

  prev.addEventListener("click", () => {
    if (weekOffset >= 52) return;
    weekOffset += 1;
    load();
  });

  next.addEventListener("click", () => {
    if (weekOffset <= 0) return;
    weekOffset -= 1;
    load();
  });

  load();
})();
