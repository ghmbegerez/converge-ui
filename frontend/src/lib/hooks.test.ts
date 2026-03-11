import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";

import { api, usePersistedState, useSnapshot } from "./hooks";

describe("api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns parsed JSON on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 }))),
    );
    const result = await api("/test");
    expect(result).toEqual({ ok: true });
  });

  it("throws on non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response("", { status: 500 }))),
    );
    await expect(api("/test")).rejects.toThrow("HTTP 500");
  });

  it("dispatches auth:expired on 401", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response("", { status: 401 }))),
    );
    const handler = vi.fn();
    window.addEventListener("auth:expired", handler);
    await expect(api("/test")).rejects.toThrow("Session expired");
    expect(handler).toHaveBeenCalled();
    window.removeEventListener("auth:expired", handler);
  });
});

describe("usePersistedState", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("returns initial value when key is absent", () => {
    const { result } = renderHook(() => usePersistedState("test-key", "default"));
    expect(result.current[0]).toBe("default");
  });

  it("reads from localStorage on init", () => {
    window.localStorage.setItem("test-key", "stored");
    const { result } = renderHook(() => usePersistedState("test-key", "default"));
    expect(result.current[0]).toBe("stored");
  });

  it("writes to localStorage on change", () => {
    const { result } = renderHook(() => usePersistedState("test-key", "default"));
    act(() => {
      result.current[1]("updated");
    });
    expect(result.current[0]).toBe("updated");
    expect(window.localStorage.getItem("test-key")).toBe("updated");
  });
});

describe("useSnapshot", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("fetches data on mount", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(JSON.stringify({ value: 42 }), { status: 200 }))),
    );
    const { result } = renderHook(() => useSnapshot("/api/test", 60000));
    await waitFor(() => {
      expect(result.current.data).toEqual({ value: 42 });
    });
    expect(result.current.error).toBeNull();
  });

  it("sets error on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response("", { status: 500 }))),
    );
    const { result } = renderHook(() => useSnapshot("/api/test", 60000));
    await waitFor(() => {
      expect(result.current.error).toBe("HTTP 500");
    });
  });
});
