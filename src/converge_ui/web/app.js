const state = {
  route: window.location.pathname,
  overview: null,
  operations: null,
  detail: null,
};

const app = document.getElementById("app");

function fetchJson(url, options) {
  return fetch(url, options).then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  });
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  return String(value);
}

function statusTone(value) {
  if (["critical", "failed", "blocked", "policy_gate"].includes(value)) {
    return "danger";
  }
  if (["high", "retry_pending", "review_required"].includes(value)) {
    return "warn";
  }
  return "ok";
}

function shell(content, banner = "") {
  const overviewActive = state.route === "/" ? "active" : "";
  const opsActive = state.route.startsWith("/operations") ? "active" : "";
  return `
    <div class="shell">
      ${banner}
      <div class="masthead">
        <section class="brand">
          <div class="hero-line"><span class="pulse"></span><span class="label">Alpha Control Plane</span></div>
          <h1>Converge UI</h1>
          <p>Runtime, riesgo y trazabilidad en una sola superficie operativa. Diseñado para decidir rápido sin perder contexto.</p>
          <div class="status-row">
            <span class="status-chip ${statusTone(state.overview?.data_source)}">${formatValue(state.overview?.data_source || "loading")}</span>
            <span class="status-chip ${state.overview?.services?.orchestrator?.reachable ? "ok" : "danger"}">orchestrator ${state.overview?.services?.orchestrator?.reachable ? "online" : "offline"}</span>
            <span class="status-chip ${state.overview?.services?.converge?.reachable ? "ok" : "warn"}">converge ${state.overview?.services?.converge?.reachable ? "online" : "degraded"}</span>
          </div>
        </section>
        <section class="snapshot">
          <div class="snapshot-meta">
            <span class="label">Snapshot</span>
            <button class="primary" id="refresh-action">Refresh</button>
          </div>
          <h3>Last generated</h3>
          <p class="code">${formatValue(state.overview?.generated_at || state.operations?.generated_at)}</p>
          <p>Hybrid mode keeps the surface alive with real data when available and demo data when infrastructure is incomplete.</p>
        </section>
      </div>
      <nav class="nav">
        <a class="${overviewActive}" href="/">Overview</a>
        <a class="${opsActive}" href="/operations">Operations</a>
      </nav>
      ${content}
    </div>
  `;
}

function renderOverview() {
  const overview = state.overview;
  const operations = state.operations;
  const alerts = overview.alerts || [];
  const blockers = overview.top_blockers || [];
  const banner = overview.data_source === "stale-cache"
    ? `<div class="banner">Showing last known snapshot while upstream services recover.</div>`
    : "";
  app.innerHTML = shell(`
    <section class="grid-kpis">
      ${renderKpi("Running", overview.kpis.running, "Live jobs currently executing")}
      ${renderKpi("Blocked", overview.kpis.blocked, "Items waiting on policy, review or intervention")}
      ${renderKpi("Retry", overview.kpis.retry_pending, "Jobs queued behind backoff")}
      ${renderKpi("Merged", overview.kpis.merged, "Successful decisions cleared by governance")}
      ${renderKpi("Failed", overview.kpis.failed, "Terminal failures requiring diagnosis")}
      ${renderKpi("Block rate", overview.kpis.block_rate, "Share of evaluations ending in a block")}
    </section>
    <section class="layout">
      <div class="stack">
        <section class="section-card">
          <div class="section-header"><span class="label">Alerts</span><span class="muted">${alerts.length} active</span></div>
          <div class="list">
            ${alerts.length ? alerts.map((alert) => `
              <div class="list-item alert">
                <div class="timeline-title">${alert.title}</div>
                <div class="code muted">${alert.code}</div>
              </div>
            `).join("") : '<div class="empty">No active alerts. The control plane is currently quiet.</div>'}
          </div>
        </section>
        <section class="section-card">
          <div class="section-header"><span class="label">Running now</span><span class="muted">${operations.running.length} jobs</span></div>
          <div class="list">
            ${operations.running.map(renderJobCard).join("")}
          </div>
        </section>
      </div>
      <div class="stack">
        <section class="section-card">
          <div class="section-header"><span class="label">Top blockers</span><span class="muted">${blockers.length} highlighted</span></div>
          <div class="list">
            ${blockers.length ? blockers.map(renderJobCard).join("") : '<div class="empty">No blockers in the current snapshot.</div>'}
          </div>
        </section>
        <section class="section-card">
          <div class="section-header"><span class="label">Recent transitions</span><span class="muted">${operations.recent_events.length} events</span></div>
          <div class="timeline">
            ${operations.recent_events.map((event) => `
              <div class="timeline-item">
                <div class="timeline-title">${formatValue(event.job_id)} · ${formatValue(event.to_state)}</div>
                <div class="muted">${formatValue(event.reason)}</div>
                <div class="code">${formatValue(event.timestamp)}</div>
              </div>
            `).join("")}
          </div>
        </section>
      </div>
    </section>
  `, banner);
  attachSharedHandlers();
}

function renderOperations() {
  const operations = state.operations;
  const banner = operations.data_source === "stale-cache"
    ? `<div class="banner">Showing cached operations while upstream data refreshes.</div>`
    : "";
  const rows = [...operations.running, ...operations.retry_queue, ...operations.blocked];
  app.innerHTML = shell(`
    <section class="layout">
      <div class="stack">
        <section class="section-card">
          <div class="section-header"><span class="label">Running</span><span class="muted">${operations.running.length}</span></div>
          <div class="list">${operations.running.map(renderJobCard).join("") || '<div class="empty">No running jobs right now.</div>'}</div>
        </section>
        <section class="section-card">
          <div class="section-header"><span class="label">Retry queue</span><span class="muted">${operations.retry_queue.length}</span></div>
          <div class="list">${operations.retry_queue.map(renderJobCard).join("") || '<div class="empty">No retries waiting.</div>'}</div>
        </section>
      </div>
      <div class="stack">
        <section class="section-card">
          <div class="section-header"><span class="label">Blocked</span><span class="muted">${operations.blocked.length}</span></div>
          <div class="list">${operations.blocked.map(renderJobCard).join("") || '<div class="empty">No blocked jobs.</div>'}</div>
        </section>
        <section class="section-card">
          <div class="section-header"><span class="label">Filters</span><span class="muted">derived from current snapshot</span></div>
          <div class="filters">
            ${(operations.filters.status || []).map((item) => `<span class="pill">${item}</span>`).join("")}
            ${(operations.filters.agent || []).map((item) => `<span class="pill">${item}</span>`).join("")}
            ${(operations.filters.risk_level || []).map((item) => `<span class="pill">${item}</span>`).join("")}
          </div>
        </section>
      </div>
    </section>
    <section class="section-card" style="margin-top: 18px;">
      <div class="section-header"><span class="label">All visible jobs</span><span class="muted">${rows.length} rows</span></div>
      <div class="stack">
        ${rows.map((row) => `
          <div class="job-row">
            <div><a href="/jobs/${row.job_id}" data-link class="job-title">${row.job_id}</a><div class="muted">${formatValue(row.prompt_preview || row.reason)}</div></div>
            <div><div class="label">status</div><div class="tag ${statusTone(row.status)}">${formatValue(row.status)}</div></div>
            <div><div class="label">agent</div><div>${formatValue(row.agent)}</div></div>
            <div><div class="label">risk</div><div>${formatValue(row.risk_level)}</div></div>
            <div><div class="label">score</div><div>${formatValue(row.risk_score)}</div></div>
            <div><div class="label">trace</div><div class="code">${formatValue(row.trace_id)}</div></div>
            <div><div class="label">updated</div><div class="code">${formatValue(row.last_activity_at || row.next_retry_at)}</div></div>
          </div>
        `).join("")}
      </div>
    </section>
  `, banner);
  attachSharedHandlers();
}

function renderJobDetail() {
  const detail = state.detail;
  const job = detail.job || {};
  const intent = detail.intent;
  const risk = detail.risk_review?.risk || {};
  const compliance = detail.risk_review?.compliance || {};
  const diagnostics = detail.risk_review?.diagnostics || [];
  app.innerHTML = shell(`
    <div class="detail-grid">
      <div class="detail-hero">
        <section class="detail-card">
          <div class="detail-header">
            <div>
              <div class="label">Job detail</div>
              <h2 style="margin: 8px 0 0;">${formatValue(job.id)}</h2>
            </div>
            <div class="tag ${statusTone(job.status)}">${formatValue(job.status)}</div>
          </div>
          <p>${formatValue(job.prompt)}</p>
          <div class="metric-row">
            ${metricBox("Trace", job.trace_id)}
            ${metricBox("Attempt", job.attempts)}
            ${metricBox("Intent", job.intent_id)}
            ${metricBox("Agent", job.agent)}
          </div>
        </section>
        <section class="detail-card">
          <div class="section-header"><span class="label">Decision</span><span class="muted">${detail.data_source}</span></div>
          <div class="metric-row">
            ${metricBox("Risk level", risk.risk_level || job.risk_level)}
            ${metricBox("Risk score", risk.risk_score || job.risk_score)}
            ${metricBox("Compliance", compliance.passed === undefined ? "n/a" : compliance.passed ? "passed" : "failed")}
            ${metricBox("Reason", job.error || "running")}
          </div>
          <div class="list" style="margin-top: 14px;">
            ${(diagnostics.length ? diagnostics : [{ title: "No diagnostics available", severity: "info" }]).map((item) => `
              <div class="list-item">
                <div class="timeline-title">${formatValue(item.title)}</div>
                <div class="muted">${formatValue(item.code || item.severity)}</div>
              </div>
            `).join("")}
          </div>
        </section>
      </div>
      <div class="detail-hero">
        <section class="detail-card">
          <div class="section-header"><span class="label">Operator actions</span><span class="muted">safe only</span></div>
          <div class="action-row">
            <button class="primary" id="refresh-action">Refresh</button>
            <button id="retry-action" ${detail.operator_actions?.retry?.enabled ? "" : "disabled"}>Retry job</button>
          </div>
          <p class="muted">${detail.operator_actions?.retry?.reason || "Retry path available."}</p>
          <p class="muted">${intent ? `Intent linked: ${intent.id}` : "No converge intent linked yet."}</p>
        </section>
        <section class="detail-card">
          <div class="section-header"><span class="label">Timeline</span><span class="muted">${detail.timeline.length} transitions</span></div>
          <div class="timeline">
            ${detail.timeline.map((event) => `
              <div class="timeline-item">
                <div class="timeline-title">${formatValue(event.from_state)} -> ${formatValue(event.to_state)}</div>
                <div class="muted">${formatValue(event.reason)}</div>
                <div class="code">${formatValue(event.timestamp)}</div>
              </div>
            `).join("")}
          </div>
        </section>
        <section class="detail-card">
          <div class="section-header"><span class="label">Intent events</span><span class="muted">${detail.intent_events.length}</span></div>
          <div class="timeline">
            ${detail.intent_events.length ? detail.intent_events.map((event) => `
              <div class="timeline-item">
                <div class="timeline-title">${formatValue(event.event_type)}</div>
                <div class="muted">${JSON.stringify(event.payload || {})}</div>
                <div class="code">${formatValue(event.timestamp)}</div>
              </div>
            `).join("") : '<div class="empty">No converge events available for this job.</div>'}
          </div>
        </section>
      </div>
    </div>
  `);
  attachSharedHandlers();
}

function renderKpi(label, value, description) {
  return `
    <section class="panel">
      <div class="panel-header"><span class="label">${label}</span><span class="muted">${description}</span></div>
      <div class="kpi-value">${formatValue(value)}</div>
    </section>
  `;
}

function renderJobCard(item) {
  return `
    <div class="list-item">
      <div class="section-header">
        <a href="/jobs/${item.job_id}" data-link class="job-title">${item.job_id}</a>
        <span class="tag ${statusTone(item.status || item.reason)}">${formatValue(item.status || item.reason)}</span>
      </div>
      <div class="muted">${formatValue(item.prompt_preview || item.reason)}</div>
      <div class="filters" style="margin-top: 10px;">
        <span class="pill">${formatValue(item.agent)}</span>
        <span class="pill">${formatValue(item.risk_level)}</span>
        <span class="pill">${formatValue(item.trace_id)}</span>
      </div>
    </div>
  `;
}

function metricBox(label, value) {
  return `
    <div class="metric-box">
      <div class="label">${label}</div>
      <div>${formatValue(value)}</div>
    </div>
  `;
}

function attachSharedHandlers() {
  document.querySelectorAll("[data-link]").forEach((node) => {
    node.addEventListener("click", (event) => {
      event.preventDefault();
      const href = event.currentTarget.getAttribute("href");
      window.history.pushState({}, "", href);
      state.route = window.location.pathname;
      bootstrap();
    });
  });

  document.querySelectorAll("#refresh-action").forEach((button) => {
    button.addEventListener("click", async () => {
      await fetchJson("/api/v1/actions/refresh", { method: "POST" });
      await loadShared();
      bootstrap();
    });
  });

  const retry = document.getElementById("retry-action");
  if (retry) {
    retry.addEventListener("click", async () => {
      const jobId = state.detail?.job?.id;
      if (!jobId) {
        return;
      }
      await fetchJson(`/api/v1/actions/jobs/${jobId}/retry`, { method: "POST" });
      await loadDetail(jobId);
      bootstrap();
    });
  }
}

async function loadShared() {
  const [overview, operations] = await Promise.all([
    fetchJson("/api/v1/overview"),
    fetchJson("/api/v1/operations"),
  ]);
  state.overview = overview;
  state.operations = operations;
}

async function loadDetail(jobId) {
  state.detail = await fetchJson(`/api/v1/jobs/${jobId}`);
}

async function bootstrap() {
  await loadShared();
  if (state.route.startsWith("/jobs/")) {
    await loadDetail(state.route.split("/").pop());
    renderJobDetail();
    return;
  }
  if (state.route.startsWith("/operations")) {
    renderOperations();
    return;
  }
  renderOverview();
}

window.addEventListener("popstate", () => {
  state.route = window.location.pathname;
  bootstrap();
});

bootstrap();
window.setInterval(() => {
  if (state.route.startsWith("/jobs/")) {
    const status = state.detail?.job?.status;
    if (status === "running" || status === "retry_pending") {
      loadDetail(state.detail.job.id).then(renderJobDetail);
    }
    return;
  }
  loadShared().then(() => {
    if (state.route.startsWith("/operations")) {
      renderOperations();
      return;
    }
    renderOverview();
  });
}, 5000);
