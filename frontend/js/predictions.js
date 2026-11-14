/* Incident risk: 24 hourly slots, high-risk highlight, last updated, refresh. */

(() => {
  const Fleet = window.Fleet;
  const main = document.getElementById("main");
  if (!Fleet || !main) return;

  main.innerHTML = `
    <div class="app">
      <header class="app-head">
        <div class="app-head__copy">
          <p class="eyebrow">Module 06 <span class="eyebrow__sep">/</span> Forecast</p>
          <h1 class="app-title">Risk forecast</h1>
          <p class="app-lede">
            Predicted incident probability for each of the next 24 hours, from
            calendar features only. High-risk hours are worth a patrol.
          </p>
        </div>
        <div class="app-actions">
          <button class="btn btn--dark" type="button" id="refresh">Refresh</button>
          <a class="btn btn--ghost" href="/analytics.html">Weekly patrols</a>
        </div>
      </header>

      <section class="app-section" aria-labelledby="forecast-title">
        <div class="panel" id="forecast-panel">
          <div class="panel__head">
            <h2 class="panel__title" id="forecast-title">Next 24 hours</h2>
            <span class="app-note" id="threshold"></span>
          </div>
          <div id="forecast" aria-live="polite">
            <p class="state" role="status">Loading the forecast…</p>
          </div>
          <div class="risk-meta" id="risk-meta"></div>
        </div>
      </section>
    </div>`;

  const forecast = document.getElementById("forecast");
  const threshold = document.getElementById("threshold");
  const meta = document.getElementById("risk-meta");
  const refresh = document.getElementById("refresh");

  const levelLabel = { high: "High risk", medium: "Medium", low: "Low" };

  function render(data) {
    const high = data.slots.filter((slot) => slot.level === "high");

    threshold.textContent = `Threshold ${(data.threshold * 100).toFixed(1)}%`;

    const cases = high
      .map((slot) => Fleet.formatLocalHour(slot.ts))
      .sort();

    const summary =
      high.length === 0
        ? "No high-risk slots in the next 24 hours."
        : `${high.length} high-risk slot${high.length === 1 ? "" : "s"} in the next 24 hours: ${cases.join(", ")}.`;

    forecast.innerHTML = `
      <div class="risk-grid" role="list">
        ${data.slots
          .map(
            (slot) => `
            <div class="risk-cell risk-cell--${slot.level}" role="listitem"
                 title="${Fleet.escapeHtml(slot.ts)} · ${(slot.probability * 100).toFixed(1)}%">
              <span class="risk-cell__hour">${Fleet.formatLocalHour(slot.ts)}</span>
              <span class="risk-cell__prob">${(slot.probability * 100).toFixed(1)}%</span>
              <span class="risk-cell__level">${levelLabel[slot.level] || slot.level}</span>
            </div>`,
          )
          .join("")}
      </div>
      <p class="risk-summary">${summary}</p>`;

    meta.innerHTML = `
      <span>Last updated ${Fleet.formatTime(data.refreshed_at, true)}</span>
      <span>·</span>
      <span>Recalculated at most once an hour</span>`;
  }

  function unavailable(message) {
    forecast.innerHTML = `
      <div class="notice notice--error" role="alert">${Fleet.escapeHtml(message)}</div>
      <p class="app-lede">Train the model once, then refresh this page:</p>
      <div class="key-box">
        <code>cd ml && python export_incidents.py && python generate_fake_incidents.py --days 180 --seed 42</code>
      </div>
      <div class="key-box">
        <code>python clean.py && python build_dataset.py && python train.py</code>
      </div>`;
    threshold.textContent = "";
    meta.innerHTML = "";
  }

  async function load() {
    refresh.disabled = true;
    Fleet.loading(forecast, "Loading the forecast…");
    try {
      const data = await Fleet.api("/api/v1/predictions/risk?hours=24");
      render(data);
    } catch (error) {
      if (error.status === 503) {
        unavailable(error.message || "Prediction model not available. Run ml/train.py.");
      } else {
        Fleet.errorState(forecast, error.message || "Could not load the forecast.");
        meta.innerHTML = "";
      }
    } finally {
      refresh.disabled = false;
    }
  }

  refresh.addEventListener("click", load);
  load();
})();
