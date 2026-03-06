import { describe, expect, it } from "vitest";

import { formatValue, toCsv, toJson, toneFor } from "./ui";

describe("ui helpers", () => {
  it("formats empty values as n/a", () => {
    expect(formatValue(null)).toBe("n/a");
    expect(formatValue(undefined)).toBe("n/a");
    expect(formatValue("")).toBe("n/a");
  });

  it("formats non-empty values as strings", () => {
    expect(formatValue(42)).toBe("42");
    expect(formatValue("blocked")).toBe("blocked");
  });

  it("assigns tones by status", () => {
    expect(toneFor("blocked")).toBe("tone-danger");
    expect(toneFor("retry_pending")).toBe("tone-warn");
    expect(toneFor("running")).toBe("tone-ok");
    expect(toneFor(undefined)).toBe("tone-neutral");
  });

  it("serializes rows to csv", () => {
    const csv = toCsv(
      [
        { job_id: "job-1", status: "blocked", reason: "policy_gate" },
        { job_id: "job-2", status: "running", reason: "ok" },
      ],
      ["job_id", "status", "reason"],
    );
    expect(csv).toContain("job_id,status,reason");
    expect(csv).toContain("job-1,blocked,policy_gate");
  });

  it("serializes payloads to pretty json", () => {
    expect(toJson({ status: "ok" })).toBe('{\n  "status": "ok"\n}');
  });
});
