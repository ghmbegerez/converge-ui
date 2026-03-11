import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import { ConnectivityBanner } from "./ConnectivityBanner";

describe("ConnectivityBanner", () => {
  afterEach(() => cleanup());

  it("renders nothing when both services are reachable", () => {
    const { container } = render(
      <ConnectivityBanner
        orchestrator={{ reachable: true }}
        converge={{ reachable: true }}
      />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("shows alert when orchestrator is unreachable", () => {
    render(
      <ConnectivityBanner
        orchestrator={{ reachable: false }}
        converge={{ reachable: true }}
      />,
    );
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByText(/orchestrator/)).toBeTruthy();
  });

  it("shows both names when both are unreachable", () => {
    render(
      <ConnectivityBanner
        orchestrator={{ reachable: false }}
        converge={{ reachable: false }}
      />,
    );
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toContain("orchestrator");
    expect(alert.textContent).toContain("converge");
  });

  it("renders nothing when props are undefined", () => {
    const { container } = render(<ConnectivityBanner />);
    expect(container.innerHTML).toBe("");
  });
});
