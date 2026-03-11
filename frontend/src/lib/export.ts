import { useCallback } from "react";

import { downloadTextFile, toCsv, toJson } from "./ui";

interface UseExportOptions<T> {
  /** Base filename without extension, e.g. "converge-ui-operations" */
  filenameBase: string;
  /** The filtered rows to export */
  rows: T[];
  /** Extra metadata to include alongside items in the JSON export */
  jsonMeta?: Record<string, unknown>;
  /** Map each row to a flat object for CSV export */
  csvRowMapper: (row: T) => Record<string, unknown>;
  /** Ordered column keys for the CSV header */
  csvColumns: string[];
}

interface UseExportReturn {
  exportJson: () => void;
  exportCsv: () => void;
}

/**
 * Reusable hook that encapsulates export-to-JSON and export-to-CSV logic.
 *
 * Usage:
 * ```ts
 * const { exportJson, exportCsv } = useExport({
 *   filenameBase: "converge-ui-operations",
 *   rows: filteredRows,
 *   jsonMeta: { generated_at: snapshot.generated_at, data_source: snapshot.data_source },
 *   csvRowMapper: (row) => ({ job_id: row.job_id, status: row.status }),
 *   csvColumns: ["job_id", "status"],
 * });
 * ```
 */
export function useExport<T>({
  filenameBase,
  rows,
  jsonMeta,
  csvRowMapper,
  csvColumns,
}: UseExportOptions<T>): UseExportReturn {
  const exportJson = useCallback(() => {
    downloadTextFile(
      `${filenameBase}.json`,
      toJson({ ...jsonMeta, items: rows }),
      "application/json",
    );
  }, [filenameBase, rows, jsonMeta]);

  const exportCsv = useCallback(() => {
    downloadTextFile(
      `${filenameBase}.csv`,
      toCsv(rows.map(csvRowMapper), csvColumns),
      "text/csv;charset=utf-8",
    );
  }, [filenameBase, rows, csvRowMapper, csvColumns]);

  return { exportJson, exportCsv };
}
