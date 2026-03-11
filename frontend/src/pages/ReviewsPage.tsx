import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { DataTable } from "../components/DataTable";
import { StaleDataBanner } from "../components/StaleDataBanner";
import { useExport } from "../lib/export";
import { api, usePersistedState, useSnapshot } from "../lib/hooks";
import { formatValue, toneFor } from "../lib/ui";
import { Frame, Metric } from "../lib/layout";
import type { ActionResponse, ReviewsPayload } from "../types";

export function ReviewsPage() {
  const { data, error } = useSnapshot<ReviewsPayload>("/api/v1/reviews");
  const [message, setMessage] = useState<string>("");
  const [intentId, setIntentId] = usePersistedState("reviews:create:intent", "intent-prod-policy");
  const [reviewer, setReviewer] = usePersistedState("reviews:create:reviewer", "ops-oncall");
  const [priority, setPriority] = usePersistedState("reviews:create:priority", "1");
  const [statusFilter, setStatusFilter] = usePersistedState("reviews:status", "all");
  const [search, setSearch] = usePersistedState("reviews:search", "");

  const filteredReviews = useMemo(() => {
    if (!data) return [];
    return data.items.filter((item) => {
      const statusOk = statusFilter === "all" || item.status === statusFilter;
      const haystack = [item.task_id, item.intent_id, item.reviewer, item.status]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      const searchOk = !search.trim() || haystack.includes(search.trim().toLowerCase());
      return statusOk && searchOk;
    });
  }, [data, statusFilter, search]);

  const csvColumns = useMemo(() => ["task_id", "intent_id", "status", "reviewer", "priority"], []);
  const csvRowMapper = useCallback((item: (typeof filteredReviews)[number]) => ({
    task_id: item.task_id,
    intent_id: item.intent_id,
    status: item.status,
    reviewer: item.reviewer,
    priority: item.priority,
  }), []);
  const jsonMeta = useMemo(() => ({
    generated_at: data?.generated_at,
    data_source: data?.data_source,
  }), [data?.generated_at, data?.data_source]);

  const { exportJson: exportReviewsJson, exportCsv: exportReviewsCsv } = useExport({
    filenameBase: "converge-ui-reviews",
    rows: filteredReviews,
    jsonMeta,
    csvRowMapper,
    csvColumns,
  });

  async function runReviewAction(path: string, body: Record<string, unknown>, opts?: { confirm?: string }) {
    if (opts?.confirm && !window.confirm(opts.confirm)) return;
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
                  <button onClick={() => runReviewAction(`/api/v1/actions/reviews/${row.task_id}/complete`, { resolution: "approved", notes: "approved from UI" }, { confirm: "Complete this review? This marks it as resolved." })}>Complete</button>
                  <button onClick={() => runReviewAction(`/api/v1/actions/reviews/${row.task_id}/escalate`, { reason: "sla_breach" }, { confirm: "Escalate this review? This will notify the escalation chain." })}>Escalate</button>
                  <button onClick={() => runReviewAction(`/api/v1/actions/reviews/${row.task_id}/cancel`, { reason: "superseded" }, { confirm: "Cancel this review? This action cannot be undone." })}>Cancel</button>
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
