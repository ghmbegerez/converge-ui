export type ReviewItem = {
  task_id: string;
  intent_id?: string;
  status?: string;
  reviewer?: string | null;
  priority?: number | null;
  resolution?: string;
  notes?: string;
};

export type JobCard = {
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

export type OverviewPayload = {
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

export type OperationsPayload = {
  running: JobCard[];
  retry_queue: JobCard[];
  blocked: JobCard[];
  recent_events: Array<Record<string, string>>;
  filters: { status: string[]; agent: string[]; risk_level: string[]; source: string[] };
  generated_at: string;
  data_source: string;
};

export type JobDetailPayload = {
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

export type IntentDetailPayload = {
  intent: Record<string, any> | null;
  events: Array<Record<string, any>>;
  risk_review: Record<string, any> | null;
  reviews?: ReviewItem[];
  review_summary?: Record<string, any> | null;
  compliance_report?: Record<string, any> | null;
  generated_at: string;
  data_source: string;
};

export type ReviewsPayload = {
  items: ReviewItem[];
  summary?: Record<string, any> | null;
  generated_at: string;
  data_source: string;
};

export type CompliancePayload = {
  report?: Record<string, any> | null;
  alerts: Array<Record<string, any>>;
  generated_at: string;
  data_source: string;
};

export type OperatorAction = {
  enabled: boolean;
  label: string;
  reason?: string | null;
  requires_confirmation: boolean;
};

export type ActionResponse = {
  status: string;
  reason?: string;
  data_source?: string;
  review?: ReviewItem;
};
