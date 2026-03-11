import { useCallback, useMemo } from "react";
import { Link } from "react-router-dom";

import { DataTable } from "../components/DataTable";
import { StaleDataBanner } from "../components/StaleDataBanner";
import { useExport } from "../lib/export";
import { usePersistedState, useSnapshot } from "../lib/hooks";
import { formatValue, toneFor } from "../lib/ui";
import { Frame } from "../lib/layout";
import type { OperationsPayload } from "../types";

import { JobCardView } from "./JobPage";

export function OperationsPage() {
  const { data, error } = useSnapshot<OperationsPayload>("/api/v1/operations");
  const [sourceFilter, setSourceFilter] = usePersistedState("operations:source", "all");
  const [statusFilter, setStatusFilter] = usePersistedState("operations:status", "all");
  const [riskFilter, setRiskFilter] = usePersistedState("operations:risk", "all");
  const [search, setSearch] = usePersistedState("operations:search", "");

  const filteredRows = useMemo(() => {
    if (!data) return [];
    const rows = [...data.running, ...data.retry_queue, ...data.blocked];
    return rows.filter((row) => {
      const sourceOk = sourceFilter === "all" || data.data_source === sourceFilter;
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
  }, [data, sourceFilter, statusFilter, riskFilter, search]);

  const csvColumns = useMemo(() => ["job_id", "status", "agent", "risk_level", "risk_score", "trace_id", "intent_id", "reason"], []);
  const csvRowMapper = useCallback((row: (typeof filteredRows)[number]) => ({
    job_id: row.job_id,
    status: row.status,
    agent: row.agent,
    risk_level: row.risk_level,
    risk_score: row.risk_score,
    trace_id: row.trace_id,
    intent_id: row.intent_id,
    reason: row.reason,
  }), []);
  const jsonMeta = useMemo(() => ({
    generated_at: data?.generated_at,
    data_source: data?.data_source,
  }), [data?.generated_at, data?.data_source]);

  const { exportJson: exportOperationsJson, exportCsv: exportOperationsCsv } = useExport({
    filenameBase: "converge-ui-operations",
    rows: filteredRows,
    jsonMeta,
    csvRowMapper,
    csvColumns,
  });

  if (!data) return <Frame><p>{error ?? "Loading..."}</p></Frame>;
  const snapshot = data;

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
