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

export function toCsv(rows: Array<Record<string, unknown>>, columns: string[]) {
  const escapeCell = (value: unknown) => {
    const normalized = value === null || value === undefined ? "" : String(value);
    if (normalized.includes(",") || normalized.includes("\"") || normalized.includes("\n")) {
      return `"${normalized.replace(/"/g, "\"\"")}"`;
    }
    return normalized;
  };

  const header = columns.join(",");
  const body = rows.map((row) => columns.map((column) => escapeCell(row[column])).join(","));
  return [header, ...body].join("\n");
}

export function toJson(data: unknown) {
  return JSON.stringify(data, null, 2);
}

export function downloadTextFile(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
