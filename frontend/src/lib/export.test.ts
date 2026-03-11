import { describe, expect, it, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";

import { useExport } from "./export";
import * as ui from "./ui";

vi.spyOn(ui, "downloadTextFile").mockImplementation(() => {});

describe("useExport", () => {
  const rows = [
    { id: "1", name: "Alice" },
    { id: "2", name: "Bob" },
  ];

  it("exports JSON with metadata and items", () => {
    const { result } = renderHook(() =>
      useExport({
        filenameBase: "test-export",
        rows,
        jsonMeta: { source: "test" },
        csvRowMapper: (r) => ({ id: r.id, name: r.name }),
        csvColumns: ["id", "name"],
      }),
    );

    act(() => result.current.exportJson());

    expect(ui.downloadTextFile).toHaveBeenCalledWith(
      "test-export.json",
      expect.stringContaining('"source": "test"'),
      "application/json",
    );
  });

  it("exports CSV with correct columns", () => {
    const { result } = renderHook(() =>
      useExport({
        filenameBase: "test-export",
        rows,
        csvRowMapper: (r) => ({ id: r.id, name: r.name }),
        csvColumns: ["id", "name"],
      }),
    );

    act(() => result.current.exportCsv());

    expect(ui.downloadTextFile).toHaveBeenCalledWith(
      "test-export.csv",
      expect.stringContaining("id,name"),
      "text/csv;charset=utf-8",
    );
  });
});
