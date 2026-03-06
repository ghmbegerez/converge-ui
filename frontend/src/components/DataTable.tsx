import type { ReactNode } from "react";

type Column<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
};

type Props<T> = {
  columns: Column<T>[];
  rows: T[];
  keyFn: (row: T) => string;
};

export function DataTable<T>({ columns, rows, keyFn }: Props<T>) {
  return (
    <div className="data-table">
      <div className="data-table-header">
        {columns.map((column) => (
          <div className="data-table-cell data-table-heading" key={column.key}>
            {column.header}
          </div>
        ))}
      </div>
      {rows.map((row) => (
        <div className="data-table-row" key={keyFn(row)}>
          {columns.map((column) => (
            <div className="data-table-cell" key={column.key}>
              {column.render(row)}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
