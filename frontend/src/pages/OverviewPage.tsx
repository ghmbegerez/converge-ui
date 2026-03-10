import { Link } from "react-router-dom";

import { StaleDataBanner } from "../components/StaleDataBanner";
import { useSnapshot } from "../lib/hooks";
import { formatValue, toneFor } from "../lib/ui";
import { Frame, Metric } from "../lib/layout";
import type { OverviewPayload, OperationsPayload, JobCard } from "../types";

import { JobCardView } from "./JobPage";

export function OverviewPage() {
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
