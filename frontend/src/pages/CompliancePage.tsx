import { StaleDataBanner } from "../components/StaleDataBanner";
import { useSnapshot } from "../lib/hooks";
import { formatValue } from "../lib/ui";
import { Frame, Metric } from "../lib/layout";
import type { CompliancePayload } from "../types";

export function CompliancePage() {
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
