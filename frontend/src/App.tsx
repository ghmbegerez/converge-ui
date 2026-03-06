import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, Route, Routes, useLocation, useParams } from "react-router-dom";

import { ConnectivityBanner } from "./components/ConnectivityBanner";
import { DataTable } from "./components/DataTable";
import { LifecycleRail } from "./components/LifecycleRail";
import { StaleDataBanner } from "./components/StaleDataBanner";
import { downloadTextFile, formatValue, toCsv, toJson, toneFor } from "./lib/ui";

type ReviewItem = {
  task_id: string;
  intent_id?: string;
  status?: string;
  reviewer?: string | null;
  priority?: number | null;
  resolution?: string;
  notes?: string;
};

type JobCard = {
  job_id: string;
  trace_id?: string;
  agent?: string;
  attempt?: number;
  status: string;
  risk_level?: string;
  risk_score?: number;
  reason?: string;
  started_at?: string;
  last_activity_at?: string;
  next_retry_at?: string;
  intent_id?: string;
  prompt_preview?: string;
};

type OverviewPayload = {
  services: {
    orchestrator: { reachable: boolean; mode?: string };
    converge: { reachable: boolean; mode?: string };
  };
  kpis: Record<string, string | number>;
  alerts: Array<{ code: string; severity?: string; title?: string }>;
  top_blockers: JobCard[];
  generated_at: string;
  data_source: string;
};

type OperationsPayload = {
  running: JobCard[];
  retry_queue: JobCard[];
  blocked: JobCard[];
  recent_events: Array<Record<string, string>>;
  filters: { status: string[]; agent: string[]; risk_level: string[]; source: string[] };
  generated_at: string;
  data_source: string;
};

type JobDetailPayload = {
  job: Record<string, any> | null;
  timeline: Array<Record<string, string>>;
  intent: Record<string, any> | null;
  intent_events: Array<Record<string, any>>;
  risk_review: Record<string, any> | null;
  reviews?: ReviewItem[];
  review_summary?: Record<string, any> | null;
  compliance_report?: Record<string, any> | null;
  operator_actions: Record<string, any>;
  generated_at: string;
  data_source: string;
};

type IntentDetailPayload = {
  intent: Record<string, any> | null;
  events: Array<Record<string, any>>;
  risk_review: Record<string, any> | null;
  reviews?: ReviewItem[];
  review_summary?: Record<string, any> | null;
  compliance_report?: Record<string, any> | null;
  generated_at: string;
  data_source: string;
};

type ReviewsPayload = {
  items: ReviewItem[];
  summary?: Record<string, any> | null;
  generated_at: string;
  data_source: string;
};

type CompliancePayload = {
  report?: Record<string, any> | null;
  alerts: Array<Record<string, any>>;
  generated_at: string;
  data_source: string;
};

type ActionResponse = {
  status: string;
  note?: string;
  reason?: string;
  data_source?: string;
  review?: ReviewItem;
};

function usePersistedState(key: string, initialValue: string) {
  const [value, setValue] = useState<string>(() => {
    if (typeof window === "undefined") {
      return initialValue;
    }
    return window.localStorage.getItem(key) ?? initialValue;
  });

  useEffect(() => {
    window.localStorage.setItem(key, value);
  }, [key, value]);

  return [value, setValue] as const;
}

async function api<T = Record<string, unknown>>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function useSnapshot<T = Record<string, unknown>>(path: string, intervalMs = 5000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const payload = await api<T>(path);
        if (active) {
          setData(payload);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      }
    };
    load();
    const timer = window.setInterval(load, intervalMs);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [path, intervalMs]);

  return { data, error };
}

function Frame({ children }: { children: React.ReactNode }) {
  const { data: overview } = useSnapshot<OverviewPayload>("/api/v1/overview");
  return (
    <div className="frame">
      <ConnectivityBanner
        orchestrator={overview?.services?.orchestrator}
        converge={overview?.services?.converge}
      />
      <header className="frame-header">
        <div className="brand">
          <p className="eyebrow">Alpha Control Plane</p>
          <h1>Converge UI</h1>
          <p className="lede">Runtime, reviews, compliance y trazabilidad en una superficie operativa única.</p>
        </div>
        <div className="chips">
          <span className={`chip ${toneFor(overview?.data_source)}`}>{overview?.data_source ?? "loading"}</span>
          <span className={`chip ${overview?.services?.orchestrator?.reachable ? "tone-ok" : "tone-danger"}`}>
            {overview?.services?.orchestrator?.reachable ? "orchestrator online" : "orchestrator offline"}
          </span>
          <span className={`chip ${overview?.services?.converge?.reachable ? "tone-ok" : "tone-warn"}`}>
            {overview?.services?.converge?.reachable ? "converge online" : "converge degraded"}
          </span>
        </div>
      </header>
      <nav className="nav">
        <NavLink to="/">Overview</NavLink>
        <NavLink to="/operations">Operations</NavLink>
        <NavLink to="/reviews">Reviews</NavLink>
        <NavLink to="/compliance">Compliance</NavLink>
      </nav>
      {children}
    </div>
  );
}

function OverviewPage() {
  const { data, error } = useSnapshot<OverviewPayload>("/api/v1/overview");
  const { data: operations } = useSnapshot<OperationsPayload>("/api/v1/operations");

  if (!data) return <Frame><p>{error ?? "Loading..."}</p></Frame>;

  return (
    <Frame>
      {data.data_source === "stale-cache" ? <StaleDataBanner message="Showing last known snapshot while upstream services recover." /> : null}
      <section className="grid six">
        {Object.entries(data.kpis).map(([key, value]) => (
          <article className="card metric" key={key}>
            <p className="eyebrow">{key}</p>
            <h2>{String(value)}</h2>
          </article>
        ))}
      </section>
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Alerts</p>
            <span>{data.alerts.length}</span>
          </div>
          <div className="stack">
            {data.alerts.length ? data.alerts.map((alert) => (
              <div className="item" key={alert.code}>
                <strong>{alert.title ?? alert.code}</strong>
                <p>{alert.code}</p>
              </div>
            )) : <div className="empty">No active alerts.</div>}
          </div>
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Top blockers</p>
            <span>{data.top_blockers.length}</span>
          </div>
          <div className="stack">
            {data.top_blockers.length ? data.top_blockers.map((row) => <JobCardView key={row.job_id} row={row} />) : <div className="empty">No blockers in this snapshot.</div>}
          </div>
        </article>
      </section>
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Governance</p>
            <span>operator lane</span>
          </div>
          <div className="grid four">
            <Metric label="Open reviews" value={data.kpis.open_reviews} />
            <Metric label="Mergeable rate" value={data.kpis.mergeable_rate} />
            <Metric label="Blocked" value={data.kpis.blocked} />
            <Metric label="Block rate" value={data.kpis.block_rate} />
          </div>
          <div className="action-bar">
            <Link className="link-button" to="/reviews">Open reviews</Link>
            <Link className="link-button" to="/compliance">Open compliance</Link>
          </div>
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Queue health</p>
            <span>{data.generated_at}</span>
          </div>
          <div className="stack">
            <div className="item">
              <strong>Orchestrator</strong>
              <p>{data.services.orchestrator.reachable ? "Healthy runtime signals available." : "Runtime unreachable."}</p>
            </div>
            <div className="item">
              <strong>Converge</strong>
              <p>{data.services.converge.reachable ? "Governance and risk data available." : "Governance path degraded."}</p>
            </div>
          </div>
        </article>
      </section>
      <article className="card">
        <div className="section-head">
          <p className="eyebrow">Recent transitions</p>
          <span>{operations?.recent_events?.length ?? 0}</span>
        </div>
        <div className="stack">
          {(operations?.recent_events ?? []).map((event, index) => (
            <div className="item" key={`${event.job_id}-${index}`}>
              <strong>{formatValue(event.job_id)} · {formatValue(event.to_state)}</strong>
              <p>{formatValue(event.reason)}</p>
              <code>{formatValue(event.timestamp)}</code>
            </div>
          ))}
        </div>
      </article>
    </Frame>
  );
}

function OperationsPage() {
  const { data, error } = useSnapshot<OperationsPayload>("/api/v1/operations");
  const [sourceFilter, setSourceFilter] = usePersistedState("operations:source", "all");
  const [statusFilter, setStatusFilter] = usePersistedState("operations:status", "all");
  const [riskFilter, setRiskFilter] = usePersistedState("operations:risk", "all");
  const [search, setSearch] = usePersistedState("operations:search", "");

  if (!data) return <Frame><p>{error ?? "Loading..."}</p></Frame>;
  const snapshot = data;

  const rows = [...snapshot.running, ...snapshot.retry_queue, ...snapshot.blocked];
  const filteredRows = rows.filter((row) => {
    const sourceOk = sourceFilter === "all" || snapshot.data_source === sourceFilter;
    const statusOk = statusFilter === "all" || row.status === statusFilter;
    const riskOk = riskFilter === "all" || row.risk_level === riskFilter;
    const haystack = [
      row.job_id,
      row.intent_id,
      row.trace_id,
      row.agent,
      row.prompt_preview,
      row.reason,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const searchOk = !search.trim() || haystack.includes(search.trim().toLowerCase());
    return sourceOk && statusOk && riskOk && searchOk;
  });

  function exportOperationsJson() {
    downloadTextFile(
      "converge-ui-operations.json",
      toJson({
        generated_at: snapshot.generated_at,
        data_source: snapshot.data_source,
        items: filteredRows,
      }),
      "application/json",
    );
  }

  function exportOperationsCsv() {
    downloadTextFile(
      "converge-ui-operations.csv",
      toCsv(
        filteredRows.map((row) => ({
          job_id: row.job_id,
          status: row.status,
          agent: row.agent,
          risk_level: row.risk_level,
          risk_score: row.risk_score,
          trace_id: row.trace_id,
          intent_id: row.intent_id,
          reason: row.reason,
        })),
        ["job_id", "status", "agent", "risk_level", "risk_score", "trace_id", "intent_id", "reason"],
      ),
      "text/csv;charset=utf-8",
    );
  }

  return (
    <Frame>
      {snapshot.data_source === "stale-cache" ? <StaleDataBanner message="Showing cached operations while upstream data refreshes." /> : null}
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Running</p>
            <span>{snapshot.running.length}</span>
          </div>
          <div className="stack">{snapshot.running.length ? snapshot.running.map((row) => <JobCardView key={row.job_id} row={row} />) : <div className="empty">No running jobs.</div>}</div>
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Retry queue</p>
            <span>{snapshot.retry_queue.length}</span>
          </div>
          <div className="stack">{snapshot.retry_queue.length ? snapshot.retry_queue.map((row) => <JobCardView key={row.job_id} row={row} />) : <div className="empty">No retries waiting.</div>}</div>
        </article>
      </section>
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Blocked</p>
            <span>{snapshot.blocked.length}</span>
          </div>
          <div className="stack">{snapshot.blocked.length ? snapshot.blocked.map((row) => <JobCardView key={row.job_id} row={row} />) : <div className="empty">No blocked work.</div>}</div>
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Filters</p>
            <span>{filteredRows.length} visible</span>
          </div>
          <div className="filter-bar">
            <label>
              <span>Search</span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="job, intent, trace, reason"
              />
            </label>
            <label>
              <span>Source</span>
              <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
                <option value="all">all</option>
                {(snapshot.filters.source ?? []).map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label>
              <span>Status</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="all">all</option>
                {(snapshot.filters.status ?? []).map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label>
              <span>Risk</span>
              <select value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)}>
                <option value="all">all</option>
                {(snapshot.filters.risk_level ?? []).map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
          </div>
          <div className="chips">
            {(snapshot.filters.agent ?? []).map((item) => <span className="chip" key={item}>{item}</span>)}
            {(snapshot.filters.risk_level ?? []).map((item) => <span className="chip" key={item}>{item}</span>)}
          </div>
          <div className="action-bar">
            <button onClick={exportOperationsCsv}>Export CSV</button>
            <button onClick={exportOperationsJson}>Export JSON</button>
          </div>
        </article>
      </section>
      <article className="card">
        <div className="section-head">
          <p className="eyebrow">All visible jobs</p>
          <span>{filteredRows.length}</span>
        </div>
        <DataTable
          columns={[
            {
              key: "job",
              header: "Job",
              render: (row) => (
                <div>
                  <Link to={`/jobs/${row.job_id}`}>{row.job_id}</Link>
                  <p>{row.prompt_preview ?? row.reason}</p>
                </div>
              ),
            },
            {
              key: "status",
              header: "Status",
              render: (row) => <span className={`chip ${toneFor(row.status)}`}>{row.status}</span>,
            },
            {
              key: "agent",
              header: "Agent",
              render: (row) => formatValue(row.agent),
            },
            {
              key: "risk",
              header: "Risk",
              render: (row) => formatValue(row.risk_level),
            },
            {
              key: "score",
              header: "Score",
              render: (row) => formatValue(row.risk_score),
            },
            {
              key: "trace",
              header: "Trace",
              render: (row) => <code>{formatValue(row.trace_id)}</code>,
            },
          ]}
          rows={filteredRows}
          keyFn={(row) => row.job_id}
        />
      </article>
    </Frame>
  );
}

function ReviewsPage() {
  const { data, error } = useSnapshot<ReviewsPayload>("/api/v1/reviews");
  const [message, setMessage] = useState<string>("");
  const [intentId, setIntentId] = usePersistedState("reviews:create:intent", "intent-prod-policy");
  const [reviewer, setReviewer] = usePersistedState("reviews:create:reviewer", "ops-oncall");
  const [priority, setPriority] = usePersistedState("reviews:create:priority", "1");
  const [statusFilter, setStatusFilter] = usePersistedState("reviews:status", "all");
  const [search, setSearch] = usePersistedState("reviews:search", "");

  async function runReviewAction(path: string, body: Record<string, unknown>) {
    const payload = await api<ActionResponse>(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    setMessage(payload.status);
  }

  async function handleCreateReview() {
    const payload = await api<ActionResponse>("/api/v1/actions/reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        intent_id: intentId,
        trigger: "policy",
        reviewer: reviewer || undefined,
        priority: Number(priority),
      }),
    });
    setMessage(payload.status);
  }

  if (!data) return <Frame><p>{error ?? "Loading..."}</p></Frame>;
  const snapshot = data;
  const filteredReviews = snapshot.items.filter((item) => {
    const statusOk = statusFilter === "all" || item.status === statusFilter;
    const haystack = [item.task_id, item.intent_id, item.reviewer, item.status]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const searchOk = !search.trim() || haystack.includes(search.trim().toLowerCase());
    return statusOk && searchOk;
  });

  function exportReviewsJson() {
    downloadTextFile(
      "converge-ui-reviews.json",
      toJson({
        generated_at: snapshot.generated_at,
        data_source: snapshot.data_source,
        items: filteredReviews,
      }),
      "application/json",
    );
  }

  function exportReviewsCsv() {
    downloadTextFile(
      "converge-ui-reviews.csv",
      toCsv(
        filteredReviews.map((item) => ({
          task_id: item.task_id,
          intent_id: item.intent_id,
          status: item.status,
          reviewer: item.reviewer,
          priority: item.priority,
        })),
        ["task_id", "intent_id", "status", "reviewer", "priority"],
      ),
      "text/csv;charset=utf-8",
    );
  }

  return (
    <Frame>
      {snapshot.data_source === "stale-cache" ? <StaleDataBanner message="Showing cached review queue while converge recovers." /> : null}
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Review queue</p>
            <span>{snapshot.items.length}</span>
          </div>
          <div className="grid four">
            <Metric label="Open" value={data.summary?.open_reviews} />
            <Metric label="Completed" value={data.summary?.completed_reviews} />
            <Metric label="Source" value={snapshot.data_source} />
            <Metric label="Generated" value={snapshot.generated_at} />
          </div>
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Create review</p>
            <span>manual trigger</span>
          </div>
          <div className="filter-bar">
            <label>
              <span>Intent</span>
              <input value={intentId} onChange={(event) => setIntentId(event.target.value)} />
            </label>
            <label>
              <span>Reviewer</span>
              <input value={reviewer} onChange={(event) => setReviewer(event.target.value)} />
            </label>
            <label>
              <span>Priority</span>
              <select value={priority} onChange={(event) => setPriority(event.target.value)}>
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
              </select>
            </label>
          </div>
          <div className="action-bar">
            <button onClick={handleCreateReview} disabled={!intentId.trim()}>Request review</button>
          </div>
          <p>Assign, complete or escalate from the same board without leaving the control plane.</p>
          {message ? <div className="banner subtle">{message}</div> : null}
        </article>
      </section>
      <article className="card">
        <div className="section-head">
          <p className="eyebrow">Review tasks</p>
          <span>{filteredReviews.length}</span>
        </div>
        <div className="filter-bar">
          <label>
            <span>Search</span>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="task, intent, reviewer"
            />
          </label>
          <label>
            <span>Status</span>
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              <option value="all">all</option>
              {Array.from(new Set(snapshot.items.map((item) => item.status).filter(Boolean))).map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="action-bar">
          <button onClick={exportReviewsCsv}>Export CSV</button>
          <button onClick={exportReviewsJson}>Export JSON</button>
        </div>
        <DataTable
          columns={[
            {
              key: "task",
              header: "Task",
              render: (row) => (
                <div>
                  <strong>{row.task_id}</strong>
                  <p>{row.intent_id ? <Link to={`/intents/${row.intent_id}`}>{row.intent_id}</Link> : "No linked intent"}</p>
                </div>
              ),
            },
            {
              key: "status",
              header: "Status",
              render: (row) => <span className={`chip ${toneFor(row.status)}`}>{formatValue(row.status)}</span>,
            },
            {
              key: "reviewer",
              header: "Reviewer",
              render: (row) => formatValue(row.reviewer),
            },
            {
              key: "priority",
              header: "Priority",
              render: (row) => formatValue(row.priority),
            },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <div className="table-actions">
                  <button onClick={() => runReviewAction(`/api/v1/actions/reviews/${row.task_id}/assign`, { reviewer: "ops-oncall" })}>Assign</button>
                  <button onClick={() => runReviewAction(`/api/v1/actions/reviews/${row.task_id}/complete`, { resolution: "approved", notes: "approved from UI" })}>Complete</button>
                  <button onClick={() => runReviewAction(`/api/v1/actions/reviews/${row.task_id}/escalate`, { reason: "sla_breach" })}>Escalate</button>
                  <button onClick={() => runReviewAction(`/api/v1/actions/reviews/${row.task_id}/cancel`, { reason: "superseded" })}>Cancel</button>
                </div>
              ),
            },
          ]}
          rows={filteredReviews}
          keyFn={(row) => row.task_id}
        />
      </article>
    </Frame>
  );
}

function CompliancePage() {
  const { data, error } = useSnapshot<CompliancePayload>("/api/v1/compliance");

  if (!data) return <Frame><p>{error ?? "Loading..."}</p></Frame>;

  return (
    <Frame>
      {data.data_source === "stale-cache" ? <StaleDataBanner message="Showing cached compliance posture while the live report refreshes." /> : null}
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Compliance posture</p>
            <span className={`chip ${data.report?.passed ? "tone-ok" : "tone-danger"}`}>{data.report?.passed ? "pass" : "attention"}</span>
          </div>
          <div className="grid four">
            <Metric label="Mergeable rate" value={data.report?.mergeable_rate} />
            <Metric label="Source" value={data.data_source} />
            <Metric label="Alerts" value={data.alerts.length} />
            <Metric label="Generated" value={data.generated_at} />
          </div>
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Current reading</p>
            <span>{data.alerts.length}</span>
          </div>
          <p>Use this panel as the merge-readiness view for the whole system. If this page is red, the queue is lying to you.</p>
        </article>
      </section>
      <article className="card">
        <div className="section-head">
          <p className="eyebrow">Compliance alerts</p>
          <span>{data.alerts.length}</span>
        </div>
        <div className="stack">
          {data.alerts.length ? data.alerts.map((alert, index) => (
            <div className="item" key={`${alert.code}-${index}`}>
              <strong>{formatValue(alert.title ?? alert.code)}</strong>
              <p>{formatValue(alert.severity)}</p>
            </div>
          )) : <div className="empty">No active compliance alerts.</div>}
        </div>
      </article>
    </Frame>
  );
}

function JobCardView({ row }: { row: JobCard }) {
  return (
    <div className="item">
      <div className="section-head">
        <Link to={`/jobs/${row.job_id}`}>{row.job_id}</Link>
        <span className={`chip ${toneFor(row.status || row.reason)}`}>{row.status}</span>
      </div>
      <p>{row.prompt_preview ?? row.reason ?? "No summary available."}</p>
      <div className="chips">
        <span className="chip">{formatValue(row.agent)}</span>
        <span className="chip">{formatValue(row.risk_level)}</span>
        <span className="chip"><code>{formatValue(row.trace_id)}</code></span>
      </div>
    </div>
  );
}

function JobPage() {
  const { jobId } = useParams();
  const interval = useMemo(() => 3000, []);
  const { data, error } = useSnapshot<JobDetailPayload>(`/api/v1/jobs/${jobId}`, interval);
  const [actionMessage, setActionMessage] = useState<string>("");

  if (!data) return <Frame><p>{error ?? "Loading..."}</p></Frame>;
  const snapshot = data;

  const risk = snapshot.risk_review?.risk ?? {};
  const compliance = snapshot.compliance_report ?? snapshot.risk_review?.compliance ?? {};
  const diagnostics = snapshot.risk_review?.diagnostics ?? [];
  const reviews = snapshot.reviews ?? [];

  async function handleRefresh() {
    const payload = await api<ActionResponse>("/api/v1/actions/refresh", { method: "POST" });
    setActionMessage(payload.note ?? payload.status);
  }

  async function handleRetry() {
    const jobIdForAction = snapshot.job?.id;
    if (!jobIdForAction) return;
    const payload = await api<ActionResponse>(`/api/v1/actions/jobs/${jobIdForAction}/retry`, { method: "POST" });
    setActionMessage(payload.reason ?? payload.status);
  }

  async function handleRequestReview() {
    const intentId = snapshot.intent?.id;
    if (!intentId) return;
    const payload = await api<ActionResponse>("/api/v1/actions/reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intent_id: intentId, trigger: "policy", priority: 1 }),
    });
    setActionMessage(payload.status);
  }

  function exportJobJson() {
    downloadTextFile(
      `converge-ui-job-${snapshot.job?.id ?? "unknown"}.json`,
      toJson(snapshot),
      "application/json",
    );
  }

  return (
    <Frame>
      {snapshot.data_source === "stale-cache" ? <StaleDataBanner message="Showing cached detail while the live path recovers." /> : null}
      <section className="two-up">
        <article className="card detail-hero">
          <div className="section-head">
            <div>
              <p className="eyebrow">Job detail</p>
              <h2>{snapshot.job?.id}</h2>
            </div>
            <span className={`chip ${toneFor(snapshot.job?.status)}`}>{formatValue(snapshot.job?.status)}</span>
          </div>
          <p>{formatValue(snapshot.job?.prompt)}</p>
          <LifecycleRail status={typeof snapshot.job?.status === "string" ? snapshot.job.status : undefined} />
          <div className="grid four">
            <Metric label="Trace" value={snapshot.job?.trace_id} />
            <Metric label="Attempt" value={snapshot.job?.attempts} />
            <Metric label="Intent" value={snapshot.job?.intent_id} />
            <Metric label="Agent" value={snapshot.job?.agent} />
          </div>
        </article>
        <article className="card detail-hero">
          <div className="section-head">
            <p className="eyebrow">Decision</p>
            <span>{snapshot.data_source}</span>
          </div>
          <div className="grid four">
            <Metric label="Risk level" value={risk.risk_level ?? snapshot.job?.risk_level} />
            <Metric label="Risk score" value={risk.risk_score ?? snapshot.job?.risk_score} />
            <Metric label="Compliance" value={compliance.passed === undefined ? "n/a" : compliance.passed ? "passed" : "failed"} />
            <Metric label="Reason" value={snapshot.job?.error ?? "running"} />
          </div>
          <div className="stack">
            {(diagnostics.length ? diagnostics : [{ title: "No diagnostics available", code: "info" }]).map((item: Record<string, unknown>, index: number) => (
              <div className="item" key={`${item.title}-${index}`}>
                <strong>{formatValue(item.title)}</strong>
                <p>{formatValue(item.code)}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Operator actions</p>
            <span>safe only</span>
          </div>
          <div className="action-bar">
            <button onClick={handleRefresh}>Refresh</button>
            <button disabled={!snapshot.operator_actions?.retry?.enabled} onClick={handleRetry}>Retry job</button>
            <button disabled={!snapshot.intent?.id} onClick={handleRequestReview}>Request review</button>
            <button onClick={exportJobJson}>Export JSON</button>
          </div>
          <p>{snapshot.operator_actions?.retry?.reason ?? "Retry path available."}</p>
          {actionMessage ? <div className="banner subtle">{actionMessage}</div> : null}
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Intent summary</p>
            <span>{snapshot.intent ? "linked" : "none"}</span>
          </div>
          <div className="stack">
            <div className="item">
              <strong>{snapshot.intent?.id ? <Link to={`/intents/${snapshot.intent.id}`}>{snapshot.intent.id}</Link> : "n/a"}</strong>
              <p>{formatValue(snapshot.intent?.status)}</p>
            </div>
            {(snapshot.intent_events ?? []).map((event, index) => (
              <div className="item" key={`${event.event_type}-${index}`}>
                <strong>{formatValue(event.event_type)}</strong>
                <p>{JSON.stringify(event.payload ?? {})}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Reviews</p>
            <span>{reviews.length}</span>
          </div>
          <div className="stack">
            {reviews.length ? reviews.map((review) => (
              <div className="item" key={review.task_id}>
                <strong>{review.task_id}</strong>
                <p>{formatValue(review.status)} · reviewer {formatValue(review.reviewer)}</p>
              </div>
            )) : <div className="empty">No review tasks linked to this job.</div>}
          </div>
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Compliance</p>
            <span>{compliance.passed ? "pass" : "attention"}</span>
          </div>
          <div className="stack">
            {(compliance.alerts ?? []).length ? (compliance.alerts ?? []).map((alert: Record<string, unknown>, index: number) => (
              <div className="item" key={`${alert.code}-${index}`}>
                <strong>{formatValue(alert.title ?? alert.code)}</strong>
                <p>{formatValue(alert.severity)}</p>
              </div>
            )) : <div className="empty">No compliance alerts on this job.</div>}
          </div>
        </article>
      </section>
      <article className="card">
        <div className="section-head">
          <p className="eyebrow">Timeline</p>
          <span>{snapshot.timeline.length}</span>
        </div>
        <div className="timeline-list">
          {snapshot.timeline.map((event, index) => (
            <div className="timeline-event" key={`${event.timestamp}-${index}`}>
              <strong>{formatValue(event.from_state)} → {formatValue(event.to_state)}</strong>
              <p>{formatValue(event.reason)}</p>
              <code>{formatValue(event.timestamp)}</code>
            </div>
          ))}
        </div>
      </article>
    </Frame>
  );
}

function IntentPage() {
  const { intentId } = useParams();
  const { data, error } = useSnapshot<IntentDetailPayload>(`/api/v1/intents/${intentId}`, 3000);
  const [actionMessage, setActionMessage] = useState<string>("");

  if (!data) return <Frame><p>{error ?? "Loading..."}</p></Frame>;
  const snapshot = data;

  const risk = snapshot.risk_review?.risk ?? {};
  const compliance = snapshot.compliance_report ?? snapshot.risk_review?.compliance ?? {};
  const reviews = snapshot.reviews ?? [];

  async function handleRequestReview() {
    if (!snapshot.intent?.id) return;
    const payload = await api<ActionResponse>("/api/v1/actions/reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intent_id: snapshot.intent.id, trigger: "policy", priority: 1 }),
    });
    setActionMessage(payload.status);
  }

  function exportIntentJson() {
    downloadTextFile(
      `converge-ui-intent-${snapshot.intent?.id ?? "unknown"}.json`,
      toJson(snapshot),
      "application/json",
    );
  }

  return (
    <Frame>
      {snapshot.data_source === "stale-cache" ? <StaleDataBanner message="Showing cached intent detail while converge recovers." /> : null}
      <section className="two-up">
        <article className="card detail-hero">
          <div className="section-head">
            <div>
              <p className="eyebrow">Intent detail</p>
              <h2>{formatValue(snapshot.intent?.id)}</h2>
            </div>
            <span className={`chip ${toneFor(snapshot.intent?.status)}`}>{formatValue(snapshot.intent?.status)}</span>
          </div>
          <div className="grid four">
            <Metric label="Risk level" value={risk.risk_level ?? snapshot.intent?.risk_level} />
            <Metric label="Risk score" value={risk.risk_score} />
            <Metric label="Priority" value={snapshot.intent?.priority} />
            <Metric label="Target" value={snapshot.intent?.target} />
          </div>
          <div className="action-bar">
            <button onClick={handleRequestReview}>Request review</button>
            <button onClick={exportIntentJson}>Export JSON</button>
          </div>
          {actionMessage ? <div className="banner subtle">{actionMessage}</div> : null}
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Compliance</p>
            <span>{compliance.passed ? "pass" : "attention"}</span>
          </div>
          <div className="stack">
            {(compliance.alerts ?? []).length ? (compliance.alerts ?? []).map((alert: Record<string, unknown>, index: number) => (
              <div className="item" key={`${alert.code}-${index}`}>
                <strong>{formatValue(alert.title ?? alert.code)}</strong>
                <p>{formatValue(alert.severity)}</p>
              </div>
            )) : <div className="empty">No compliance alerts attached to this intent.</div>}
          </div>
        </article>
      </section>
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Intent events</p>
            <span>{snapshot.events.length}</span>
          </div>
          <div className="stack">
            {snapshot.events.map((event, index) => (
              <div className="item" key={`${event.event_type}-${index}`}>
                <strong>{formatValue(event.event_type)}</strong>
                <p>{JSON.stringify(event.payload ?? {})}</p>
              </div>
            ))}
          </div>
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Reviews</p>
            <span>{reviews.length}</span>
          </div>
          <div className="stack">
            {reviews.length ? reviews.map((review) => (
              <div className="item" key={review.task_id}>
                <strong>{review.task_id}</strong>
                <p>{formatValue(review.status)} · reviewer {formatValue(review.reviewer)}</p>
              </div>
            )) : <div className="empty">No review tasks linked to this intent.</div>}
          </div>
        </article>
      </section>
    </Frame>
  );
}

function Metric({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="metric-box">
      <p className="eyebrow">{label}</p>
      <strong>{formatValue(value)}</strong>
    </div>
  );
}

export function App() {
  const location = useLocation();

  useEffect(() => {
    document.title = `Converge UI · ${location.pathname}`;
  }, [location.pathname]);

  return (
    <Routes>
      <Route path="/" element={<OverviewPage />} />
      <Route path="/operations" element={<OperationsPage />} />
      <Route path="/reviews" element={<ReviewsPage />} />
      <Route path="/compliance" element={<CompliancePage />} />
      <Route path="/jobs/:jobId" element={<JobPage />} />
      <Route path="/intents/:intentId" element={<IntentPage />} />
    </Routes>
  );
}
