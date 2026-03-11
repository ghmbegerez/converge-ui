import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { LifecycleRail } from "../components/LifecycleRail";
import { StaleDataBanner } from "../components/StaleDataBanner";
import { api, useSnapshot } from "../lib/hooks";
import { downloadTextFile, formatValue, toJson, toneFor } from "../lib/ui";
import { Frame, Metric } from "../lib/layout";
import type { ActionResponse, JobCard, JobDetailPayload } from "../types";

export function JobCardView({ row }: { row: JobCard }) {
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

export function JobPage() {
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
    setActionMessage(payload.reason ?? payload.status);
  }

  async function handleRetry() {
    const jobIdForAction = snapshot.job?.id;
    if (!jobIdForAction) return;
    if (snapshot.operator_actions?.retry?.requires_confirmation) {
      if (!window.confirm("Retry this job? This will re-queue the job for another attempt.")) return;
    }
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
