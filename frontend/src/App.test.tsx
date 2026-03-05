import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { App } from "./App";


const overviewPayload = {
  services: {
    orchestrator: { reachable: true, mode: "real" },
    converge: { reachable: false, mode: "partial" },
  },
  kpis: {
    running: 3,
    blocked: 2,
    retry_pending: 1,
    merged: 8,
    failed: 0,
    uptime_seconds: 120,
    block_rate: 0.2,
  },
  alerts: [{ code: "service_down", title: "Converge unavailable" }],
  top_blockers: [{ job_id: "job-prod-policy", status: "blocked", reason: "policy_gate", agent: "codex", risk_level: "critical", trace_id: "tr-1" }],
  generated_at: "2026-03-05T12:00:00Z",
  data_source: "demo",
};

const operationsPayload = {
  running: [{ job_id: "job-auth-sync", status: "running", prompt_preview: "Auth session work", agent: "codex", trace_id: "tr-auth" }],
  retry_queue: [{ job_id: "job-retry", status: "retry_pending", reason: "merge_conflict", agent: "claude", trace_id: "tr-retry" }],
  blocked: [{ job_id: "job-prod-policy", status: "blocked", reason: "policy_gate", agent: "codex", risk_level: "critical", trace_id: "tr-block" }],
  recent_events: [{ job_id: "job-prod-policy", to_state: "blocked", reason: "policy gate", timestamp: "2026-03-05T12:00:00Z" }],
  filters: {
    status: ["running", "retry_pending", "blocked"],
    agent: ["codex", "claude"],
    risk_level: ["critical"],
    source: ["demo"],
  },
  generated_at: "2026-03-05T12:00:00Z",
  data_source: "demo",
};

const jobPayload = {
  job: {
    id: "job-prod-policy",
    status: "blocked",
    prompt: "Open a fast path to production branch despite missing security attestations.",
    trace_id: "tr-prod-policy",
    attempts: 1,
    intent_id: "intent-prod-policy",
    agent: "codex",
    error: "policy_gate",
  },
  timeline: [
    { from_state: "evaluated", to_state: "blocked", reason: "policy gate", timestamp: "2026-03-05T12:00:00Z" },
  ],
  intent: { id: "intent-prod-policy", status: "REJECTED" },
  intent_events: [
    { event_type: "POLICY_EVALUATED", payload: { verdict: "BLOCK" } },
  ],
  risk_review: {
    risk: { risk_level: "critical", risk_score: 82.4 },
    compliance: { passed: false },
    diagnostics: [{ title: "Production fast path violates policy guardrail", code: "policy.fastpath" }],
  },
  operator_actions: {
    retry: { enabled: true, reason: null },
  },
  generated_at: "2026-03-05T12:00:00Z",
  data_source: "stale-cache",
};


function renderAt(path: string) {
  window.history.pushState({}, "", path);
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}


describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url === "/api/v1/overview") {
          return Promise.resolve(new Response(JSON.stringify(overviewPayload), { status: 200 }));
        }
        if (url === "/api/v1/operations") {
          return Promise.resolve(new Response(JSON.stringify(operationsPayload), { status: 200 }));
        }
        if (url === "/api/v1/jobs/job-prod-policy") {
          return Promise.resolve(new Response(JSON.stringify(jobPayload), { status: 200 }));
        }
        if (url === "/api/v1/actions/refresh" && init?.method === "POST") {
          return Promise.resolve(new Response(JSON.stringify({ status: "ok", note: "refreshed" }), { status: 200 }));
        }
        if (url === "/api/v1/actions/jobs/job-prod-policy/retry" && init?.method === "POST") {
          return Promise.resolve(new Response(JSON.stringify({ status: "disabled", reason: "Retry is not exposed by the current orchestrator API." }), { status: 200 }));
        }
        return Promise.resolve(new Response(JSON.stringify({ error: "not found" }), { status: 404 }));
      }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders overview metrics and alerts", async () => {
    renderAt("/");
    await waitFor(() => {
      expect(screen.getByText("Converge UI")).toBeTruthy();
    });
    expect(screen.getByText("Converge unavailable")).toBeTruthy();
    expect(screen.getByText("job-prod-policy")).toBeTruthy();
  });

  it("renders operations board with visible jobs", async () => {
    renderAt("/operations");
    await waitFor(() => {
      expect(screen.getByText("All visible jobs")).toBeTruthy();
    });
    expect(screen.getAllByText("job-auth-sync").length).toBeGreaterThan(0);
    expect(screen.getAllByText("job-retry").length).toBeGreaterThan(0);
    expect(screen.getAllByText("job-prod-policy").length).toBeGreaterThan(0);
  });

  it("renders job detail and stale cache banner", async () => {
    renderAt("/jobs/job-prod-policy");
    await waitFor(() => {
      expect(screen.getByText("Job detail")).toBeTruthy();
    });
    expect(screen.getByText("Showing cached detail while the live path recovers.")).toBeTruthy();
    expect(screen.getByText("Production fast path violates policy guardrail")).toBeTruthy();
    expect(screen.getByText("Intent summary")).toBeTruthy();
  });
});
