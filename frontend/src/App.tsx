import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, Route, Routes, useLocation, useParams } from "react-router-dom";

import { formatValue, toneFor } from "./lib/ui";

type Json = Record<string, unknown>;

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
  operator_actions: Record<string, any>;
  generated_at: string;
  data_source: string;
};

async function api<T = Json>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function useSnapshot<T = Json>(path: string, intervalMs = 5000) {
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
      <header className="frame-header">
        <div className="brand">
          <p className="eyebrow">Alpha Control Plane</p>
          <h1>Converge UI</h1>
          <p className="lede">Runtime, riesgo y trazabilidad en una superficie operativa única.</p>
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
      {data.data_source === "stale-cache" ? <div className="banner">Showing last known snapshot while upstream services recover.</div> : null}
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
  const [sourceFilter, setSourceFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  if (!data) return <Frame><p>{error ?? "Loading..."}</p></Frame>;

  const rows = [...data.running, ...data.retry_queue, ...data.blocked];
  const filteredRows = rows.filter((row) => {
    const sourceOk = sourceFilter === "all" || data.data_source === sourceFilter;
    const statusOk = statusFilter === "all" || row.status === statusFilter;
    return sourceOk && statusOk;
  });

  return (
    <Frame>
      {data.data_source === "stale-cache" ? <div className="banner">Showing cached operations while upstream data refreshes.</div> : null}
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Running</p>
            <span>{data.running.length}</span>
          </div>
          <div className="stack">{data.running.length ? data.running.map((row) => <JobCardView key={row.job_id} row={row} />) : <div className="empty">No running jobs.</div>}</div>
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Retry queue</p>
            <span>{data.retry_queue.length}</span>
          </div>
          <div className="stack">{data.retry_queue.length ? data.retry_queue.map((row) => <JobCardView key={row.job_id} row={row} />) : <div className="empty">No retries waiting.</div>}</div>
        </article>
      </section>
      <section className="two-up">
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Blocked</p>
            <span>{data.blocked.length}</span>
          </div>
          <div className="stack">{data.blocked.length ? data.blocked.map((row) => <JobCardView key={row.job_id} row={row} />) : <div className="empty">No blocked work.</div>}</div>
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Filters</p>
            <span>{filteredRows.length} visible</span>
          </div>
          <div className="filter-bar">
            <label>
              <span>Source</span>
              <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
                <option value="all">all</option>
                {(data.filters.source ?? []).map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
            <label>
              <span>Status</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="all">all</option>
                {(data.filters.status ?? []).map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
            </label>
          </div>
          <div className="chips">
            {(data.filters.agent ?? []).map((item) => <span className="chip" key={item}>{item}</span>)}
            {(data.filters.risk_level ?? []).map((item) => <span className="chip" key={item}>{item}</span>)}
          </div>
        </article>
      </section>
      <article className="card">
        <div className="section-head">
          <p className="eyebrow">All visible jobs</p>
          <span>{filteredRows.length}</span>
        </div>
        <div className="table">
          {filteredRows.map((row) => (
            <div className="table-row" key={row.job_id}>
              <div>
                <Link to={`/jobs/${row.job_id}`}>{row.job_id}</Link>
                <p>{row.prompt_preview ?? row.reason}</p>
              </div>
              <div><span className={`chip ${toneFor(row.status)}`}>{row.status}</span></div>
              <div>{formatValue(row.agent)}</div>
              <div>{formatValue(row.risk_level)}</div>
              <div>{formatValue(row.risk_score)}</div>
              <div><code>{formatValue(row.trace_id)}</code></div>
            </div>
          ))}
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

  const risk = data.risk_review?.risk ?? {};
  const compliance = data.risk_review?.compliance ?? {};
  const diagnostics = data.risk_review?.diagnostics ?? [];

  async function handleRefresh() {
    const payload = await api<{ status: string; note?: string }>("/api/v1/actions/refresh", { method: "POST" });
    setActionMessage(payload.note ?? payload.status);
  }

  async function handleRetry() {
    const jobIdForAction = data?.job?.id;
    if (!jobIdForAction) return;
    const payload = await api<{ reason?: string; status: string }>(`/api/v1/actions/jobs/${jobIdForAction}/retry`, { method: "POST" });
    setActionMessage(payload.reason ?? payload.status);
  }

  return (
    <Frame>
      {data.data_source === "stale-cache" ? <div className="banner">Showing cached detail while the live path recovers.</div> : null}
      <section className="two-up">
        <article className="card detail-hero">
          <div className="section-head">
            <div>
              <p className="eyebrow">Job detail</p>
              <h2>{data.job?.id}</h2>
            </div>
            <span className={`chip ${toneFor(data.job?.status)}`}>{formatValue(data.job?.status)}</span>
          </div>
          <p>{formatValue(data.job?.prompt)}</p>
          <div className="grid four">
            <Metric label="Trace" value={data.job?.trace_id} />
            <Metric label="Attempt" value={data.job?.attempts} />
            <Metric label="Intent" value={data.job?.intent_id} />
            <Metric label="Agent" value={data.job?.agent} />
          </div>
        </article>
        <article className="card detail-hero">
          <div className="section-head">
            <p className="eyebrow">Decision</p>
            <span>{data.data_source}</span>
          </div>
          <div className="grid four">
            <Metric label="Risk level" value={risk.risk_level ?? data.job?.risk_level} />
            <Metric label="Risk score" value={risk.risk_score ?? data.job?.risk_score} />
            <Metric label="Compliance" value={compliance.passed === undefined ? "n/a" : compliance.passed ? "passed" : "failed"} />
            <Metric label="Reason" value={data.job?.error ?? "running"} />
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
            <button disabled={!data.operator_actions?.retry?.enabled} onClick={handleRetry}>Retry job</button>
          </div>
          <p>{data.operator_actions?.retry?.reason ?? "Retry path available."}</p>
          {actionMessage ? <div className="banner subtle">{actionMessage}</div> : null}
        </article>
        <article className="card">
          <div className="section-head">
            <p className="eyebrow">Intent summary</p>
            <span>{data.intent ? "linked" : "none"}</span>
          </div>
          <div className="stack">
            <div className="item">
              <strong>{formatValue(data.intent?.id)}</strong>
              <p>{formatValue(data.intent?.status)}</p>
            </div>
            {(data.intent_events ?? []).map((event, index) => (
              <div className="item" key={`${event.event_type}-${index}`}>
                <strong>{formatValue(event.event_type)}</strong>
                <p>{JSON.stringify(event.payload ?? {})}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
      <article className="card">
        <div className="section-head">
          <p className="eyebrow">Timeline</p>
          <span>{data.timeline.length}</span>
        </div>
        <div className="stack">
          {data.timeline.map((event, index) => (
            <div className="item" key={`${event.timestamp}-${index}`}>
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
      <Route path="/jobs/:jobId" element={<JobPage />} />
    </Routes>
  );
}
