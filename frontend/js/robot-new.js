/* Register a robot (admins only) and show its API key exactly once. */

(() => {
  const Fleet = window.Fleet;
  const main = document.getElementById("main");
  if (!Fleet || !main) return;

  const user = Fleet.user();
  if (!user || user.role !== "admin") {
    main.innerHTML = `
      <div class="app registered">
        <header class="app-head">
          <div class="app-head__copy">
            <p class="eyebrow">Module 01 <span class="eyebrow__sep">/</span> Registry</p>
            <h1 class="app-title">Not allowed</h1>
            <p class="app-lede">Only an admin can register a robot for this company.</p>
          </div>
          <div class="app-actions">
            <a class="btn btn--outline" href="/robots.html">Back to the fleet</a>
          </div>
        </header>
      </div>`;
    return;
  }

  main.innerHTML = `
    <div class="app registered">
      <header class="app-head">
        <div class="app-head__copy">
          <p class="eyebrow">Module 01 <span class="eyebrow__sep">/</span> Registry</p>
          <h1 class="app-title">Register a robot</h1>
          <p class="app-lede">
            Give the unit a name and a unique serial number. The API key is
            generated once, shown once, and stored only as a hash.
          </p>
        </div>
        <div class="app-actions">
          <a class="btn btn--ghost" href="/robots.html">Cancel</a>
        </div>
      </header>

      <section class="app-section">
        <div class="panel">
          <div id="notice"></div>
          <form id="robot-form" novalidate>
            <div class="form-grid">
              <div class="field">
                <label for="name">Robot name</label>
                <input class="input" id="name" name="name" maxlength="100" required placeholder="Atlas" />
                <p class="field__error" data-error="name"></p>
              </div>
              <div class="field">
                <label for="serial">Serial number</label>
                <input
                  class="input"
                  id="serial"
                  name="serial"
                  maxlength="50"
                  required
                  pattern="[A-Za-z0-9_-]+"
                  placeholder="ATLAS-001"
                />
                <p class="field__hint">3 to 50 letters, digits, dashes, or underscores.</p>
                <p class="field__error" data-error="serial"></p>
              </div>
              <div class="field field--actions">
                <button class="btn btn--dark" type="submit" id="submit">Register robot</button>
              </div>
            </div>
          </form>
        </div>
      </section>
    </div>`;

  const form = document.getElementById("robot-form");
  const nameInput = document.getElementById("name");
  const serialInput = document.getElementById("serial");
  const notice = document.getElementById("notice");
  const submit = document.getElementById("submit");
  const errors = {
    name: document.querySelector('[data-error="name"]'),
    serial: document.querySelector('[data-error="serial"]'),
  };

  function clearErrors() {
    Object.values(errors).forEach((element) => {
      element.textContent = "";
    });
    nameInput.removeAttribute("aria-invalid");
    serialInput.removeAttribute("aria-invalid");
  }

  function validate(name, serial) {
    clearErrors();
    let ok = true;

    if (!name) {
      errors.name.textContent = "A name is required.";
      nameInput.setAttribute("aria-invalid", "true");
      ok = false;
    } else if (name.length > 100) {
      errors.name.textContent = "Keep the name under 100 characters.";
      nameInput.setAttribute("aria-invalid", "true");
      ok = false;
    }

    if (!/^[A-Za-z0-9_-]{3,50}$/.test(serial)) {
      errors.serial.textContent =
        "Use 3 to 50 letters, digits, dashes, or underscores.";
      serialInput.setAttribute("aria-invalid", "true");
      ok = false;
    }

    return ok;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    Fleet.notice(notice, "");

    const name = nameInput.value.trim();
    const serial = serialInput.value.trim();
    if (!validate(name, serial)) return;

    submit.disabled = true;
    submit.textContent = "Registering…";

    try {
      const robot = await Fleet.api("/api/v1/robots", {
        method: "POST",
        body: JSON.stringify({ name, serial_number: serial }),
      });
      showRegistered(robot);
    } catch (error) {
      Fleet.notice(notice, error.message || "Could not register this robot.");
      if (error.status === 409) {
        errors.serial.textContent = error.message;
        serialInput.setAttribute("aria-invalid", "true");
        serialInput.focus();
      }
      submit.disabled = false;
      submit.textContent = "Register robot";
    }
  });

  function showRegistered(robot) {
    main.innerHTML = `
      <div class="app registered">
        <header class="app-head">
          <div class="app-head__copy">
            <p class="eyebrow">Registry <span class="eyebrow__sep">/</span> Registered</p>
            <h1 class="app-title">Robot registered</h1>
            <p class="app-lede">
              <strong>${Fleet.escapeHtml(robot.name)}</strong> (${Fleet.escapeHtml(robot.serial_number)})
              is now part of your fleet. Give this key to the robot or the simulator.
            </p>
          </div>
          <div class="app-actions">
            <a class="btn btn--dark" href="/robots.html">Back to the fleet <span class="btn__arrow" aria-hidden="true">→</span></a>
          </div>
        </header>

        <section class="app-section">
          <div class="panel">
            <p class="eyebrow">API key</p>
            <div class="key-box">
              <code id="api-key">${Fleet.escapeHtml(robot.api_key)}</code>
              <button class="btn btn--outline btn--sm" type="button" id="copy-key">Copy</button>
            </div>

            <p class="warning">
              <span aria-hidden="true">!</span>
              <span><strong>Save this key now.</strong> It will not be shown again. Only its hash is stored.</span>
            </p>

            <div class="app-section__head" style="margin-top: 1.5rem; margin-bottom: 0.4rem">
              <p class="app-section__title">Run the simulator</p>
            </div>
            <p class="app-lede">
              From <span class="mono">backend/</span>, paste the key into this command:
            </p>
            <div class="key-box">
              <code id="sim-command">python -m scripts.simulator --api-url http://localhost:8000 --key ${Fleet.escapeHtml(robot.api_key)}</code>
              <button class="btn btn--ghost btn--sm" type="button" id="copy-command">Copy</button>
            </div>
          </div>
        </section>
      </div>`;

    const copy = async (text, button) => {
      try {
        await navigator.clipboard.writeText(text);
      } catch {
        const area = document.createElement("textarea");
        area.value = text;
        document.body.append(area);
        area.select();
        document.execCommand("copy");
        area.remove();
      }
      const label = button.textContent;
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.textContent = label;
      }, 1600);
    };

    const keyButton = document.getElementById("copy-key");
    keyButton.addEventListener("click", () =>
      copy(document.getElementById("api-key").textContent, keyButton),
    );

    const commandButton = document.getElementById("copy-command");
    commandButton.addEventListener("click", () =>
      copy(document.getElementById("sim-command").textContent, commandButton),
    );
  }
})();
