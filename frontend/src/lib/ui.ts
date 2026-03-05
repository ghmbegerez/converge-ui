export function toneFor(value?: string | null) {
  if (!value) return "tone-neutral";
  if (["critical", "failed", "blocked", "policy_gate"].includes(value)) return "tone-danger";
  if (["high", "retry_pending", "review_required", "demo", "stale-cache"].includes(value)) return "tone-warn";
  return "tone-ok";
}

export function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "n/a";
  return String(value);
}
