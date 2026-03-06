import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";

import { ErrorBoundary } from "./ErrorBoundary";

function Thrower({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("test-error");
  }
  return <div>Normal content</div>;
}

describe("ErrorBoundary", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders children when no error", () => {
    render(
      <ErrorBoundary pageName="Test">
        <Thrower shouldThrow={false} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Normal content")).toBeTruthy();
  });

  it("renders error UI when child throws", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <ErrorBoundary pageName="TestPage">
        <Thrower shouldThrow={true} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Something went wrong")).toBeTruthy();
    expect(screen.getByText(/TestPage/)).toBeTruthy();
    expect(screen.getByText("test-error")).toBeTruthy();
    consoleSpy.mockRestore();
  });

  it("shows try again button that resets error state", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const { rerender } = render(
      <ErrorBoundary pageName="TestPage">
        <Thrower shouldThrow={true} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Something went wrong")).toBeTruthy();

    // Click try again (will throw again since shouldThrow is still true)
    fireEvent.click(screen.getByText("Try again"));
    // Error boundary catches again
    expect(screen.getByText("Something went wrong")).toBeTruthy();
    consoleSpy.mockRestore();
  });

  it("renders custom fallback when provided", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <ErrorBoundary pageName="Test" fallback={<div>Custom fallback</div>}>
        <Thrower shouldThrow={true} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("Custom fallback")).toBeTruthy();
    consoleSpy.mockRestore();
  });
});
