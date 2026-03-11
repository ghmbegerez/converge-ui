import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import { DataTable } from "./DataTable";

type Row = { id: string; name: string };

const columns = [
  { key: "id", header: "ID", render: (r: Row) => r.id },
  { key: "name", header: "Name", render: (r: Row) => r.name },
];

describe("DataTable", () => {
  afterEach(() => cleanup());

  it("renders headers and rows", () => {
    const rows: Row[] = [
      { id: "1", name: "Alice" },
      { id: "2", name: "Bob" },
    ];
    render(<DataTable columns={columns} rows={rows} keyFn={(r) => r.id} />);
    expect(screen.getByText("ID")).toBeTruthy();
    expect(screen.getByText("Name")).toBeTruthy();
    expect(screen.getByText("Alice")).toBeTruthy();
    expect(screen.getByText("Bob")).toBeTruthy();
  });

  it("renders headers only when rows are empty", () => {
    render(<DataTable columns={columns} rows={[]} keyFn={(r: Row) => r.id} />);
    expect(screen.getByText("ID")).toBeTruthy();
    expect(screen.queryByText("Alice")).toBeNull();
  });
});
