import { NavLink } from "react-router-dom";

import { ConnectivityBanner } from "../components/ConnectivityBanner";
import { useSnapshot } from "./hooks";
import { formatValue, toneFor } from "./ui";
import type { OverviewPayload } from "../types";

export function Frame({ children }: { children: React.ReactNode }) {
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

export function Metric({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="metric-box">
      <p className="eyebrow">{label}</p>
      <strong>{formatValue(value)}</strong>
    </div>
  );
}
