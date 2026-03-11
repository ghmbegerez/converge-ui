import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { LifecycleRail } from "./LifecycleRail";

describe("LifecycleRail", () => {
  it("marks completed steps as done when status is running", () => {
    const { container } = render(<LifecycleRail status="running" />);
    const nodes = container.querySelectorAll(".lifecycle-node");
    // queued(done), claimed(done), running(active), evaluated, merged
    expect(nodes[0].classList.contains("done")).toBe(true);
    expect(nodes[1].classList.contains("done")).toBe(true);
    expect(nodes[2].classList.contains("active")).toBe(true);
  });

  it("shows branch node for blocked status", () => {
    render(<LifecycleRail status="blocked" />);
    expect(screen.getByText("blocked")).toBeTruthy();
  });

  it("shows branch node for failed status", () => {
    render(<LifecycleRail status="failed" />);
    expect(screen.getByText("failed")).toBeTruthy();
  });

  it("renders no active or branch when status is undefined", () => {
    const { container } = render(<LifecycleRail />);
    expect(container.querySelector(".active")).toBeNull();
    expect(container.querySelector(".branch")).toBeNull();
  });

  it("marks all steps done when status is merged", () => {
    const { container } = render(<LifecycleRail status="merged" />);
    const nodes = container.querySelectorAll(".lifecycle-node");
    // All 5 steps: queued, claimed, running, evaluated should be done, merged should be active
    expect(nodes[0].classList.contains("done")).toBe(true);
    expect(nodes[3].classList.contains("done")).toBe(true);
    expect(nodes[4].classList.contains("active")).toBe(true);
  });
});
