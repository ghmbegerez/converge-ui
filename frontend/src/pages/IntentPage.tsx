import { useState } from "react";
import { useParams } from "react-router-dom";

import { StaleDataBanner } from "../components/StaleDataBanner";
import { api, useSnapshot } from "../lib/hooks";
import { downloadTextFile, formatValue, toJson, toneFor } from "../lib/ui";
import { Frame, Metric } from "../lib/layout";
import type { ActionResponse, IntentDetailPayload } from "../types";

export function IntentPage() {
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
