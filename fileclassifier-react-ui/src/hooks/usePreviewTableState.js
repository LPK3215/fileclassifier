import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { MAX_COLUMN_WIDTH, MIN_COLUMN_WIDTH, clamp, compareCellValues } from "../lib/ui-helpers";

export default function usePreviewTableState({ frameColumns, frameRows }) {
  const [viewerField, setViewerField] = useState("__all__");
  const [viewerKeyword, setViewerKeyword] = useState("");
  const [columnFilters, setColumnFilters] = useState({});
  const [sortState, setSortState] = useState({ column: "", direction: "" });
  const [pinnedColumns, setPinnedColumns] = useState([]);
  const [columnWidths, setColumnWidths] = useState({});
  const [isResizingColumn, setIsResizingColumn] = useState(false);
  const resizeSessionRef = useRef(null);

  const getColumnWidth = useCallback(
    (columnName) => {
      const customWidth = columnWidths[columnName];
      if (typeof customWidth === "number") {
        return customWidth;
      }
      // Keep default columns compact; user can still drag to enlarge when needed.
      // const fallbackWidth = 74 + Math.min(String(columnName).length, 20) * 4;
      // return clamp(fallbackWidth, 98, 190);
      const fallbackWidth = 92 + Math.min(String(columnName).length, 20) * 5;
      return clamp(fallbackWidth, 122, 220);
    },
    [columnWidths]
  );

  const orderedColumns = useMemo(() => {
    const pinnedSet = new Set(pinnedColumns);
    const pinnedInTableOrder = frameColumns.filter((column) => pinnedSet.has(column));
    const normalColumns = frameColumns.filter((column) => !pinnedSet.has(column));
    return [...pinnedInTableOrder, ...normalColumns];
  }, [frameColumns, pinnedColumns]);

  const pinnedSet = useMemo(() => new Set(pinnedColumns), [pinnedColumns]);

  const pinnedLeftMap = useMemo(() => {
    const leftMap = {};
    let currentLeft = 0;
    for (const column of orderedColumns) {
      if (!pinnedSet.has(column)) {
        continue;
      }
      leftMap[column] = currentLeft;
      currentLeft += getColumnWidth(column);
    }
    return leftMap;
  }, [orderedColumns, pinnedSet, getColumnWidth]);

  const lastPinnedColumn = useMemo(() => {
    const pinnedInOrder = orderedColumns.filter((column) => pinnedSet.has(column));
    return pinnedInOrder.length ? pinnedInOrder[pinnedInOrder.length - 1] : "";
  }, [orderedColumns, pinnedSet]);

  const displayedRows = useMemo(() => {
    const keyword = viewerKeyword.trim().toLowerCase();
    const activeColumnFilters = Object.entries(columnFilters).filter(([, value]) => value.trim() !== "");

    let rows = frameRows.filter((row) => {
      if (keyword) {
        if (viewerField !== "__all__") {
          const target = String(row[viewerField] ?? "").toLowerCase();
          if (!target.includes(keyword)) {
            return false;
          }
        } else {
          const anyMatched = Object.values(row).some((value) =>
            String(value ?? "").toLowerCase().includes(keyword)
          );
          if (!anyMatched) {
            return false;
          }
        }
      }

      return activeColumnFilters.every(([column, filterValue]) =>
        String(row[column] ?? "").toLowerCase().includes(filterValue.trim().toLowerCase())
      );
    });

    if (sortState.column && sortState.direction) {
      rows = [...rows].sort((left, right) => {
        const compared = compareCellValues(left[sortState.column], right[sortState.column]);
        return sortState.direction === "asc" ? compared : -compared;
      });
    }

    return rows;
  }, [frameRows, viewerField, viewerKeyword, columnFilters, sortState]);

  const fieldOptions = useMemo(
    () => frameColumns.map((field) => ({ value: field, label: field })),
    [frameColumns]
  );
  const viewerFieldOptions = useMemo(
    () => [{ value: "__all__", label: "全部字段" }, ...fieldOptions],
    [fieldOptions]
  );

  function updateColumnFilter(columnName, value) {
    setColumnFilters((prev) => ({ ...prev, [columnName]: value }));
  }

  function toggleSort(columnName) {
    setSortState((prev) => {
      if (prev.column !== columnName) {
        return { column: columnName, direction: "asc" };
      }
      if (prev.direction === "asc") {
        return { column: columnName, direction: "desc" };
      }
      if (prev.direction === "desc") {
        return { column: "", direction: "" };
      }
      return { column: columnName, direction: "asc" };
    });
  }

  function togglePinColumn(columnName) {
    setPinnedColumns((prev) =>
      prev.includes(columnName) ? prev.filter((item) => item !== columnName) : [...prev, columnName]
    );
  }

  function resetColumnFilters() {
    setColumnFilters({});
  }

  function resetSort() {
    setSortState({ column: "", direction: "" });
  }

  function clearPinnedColumns() {
    setPinnedColumns([]);
  }

  function resetViewerSearch() {
    setViewerField("__all__");
    setViewerKeyword("");
  }

  function resetTableControls() {
    setColumnFilters({});
    setSortState({ column: "", direction: "" });
    setPinnedColumns([]);
    setColumnWidths({});
  }

  function handleColumnResizeStart(event, columnName) {
    if (event.button !== 0) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    resizeSessionRef.current = {
      columnName,
      startX: event.clientX,
      startWidth: getColumnWidth(columnName)
    };
    setIsResizingColumn(true);
  }

  function getSortIndicator(columnName) {
    if (sortState.column !== columnName) {
      return "↕";
    }
    return sortState.direction === "asc" ? "↑" : "↓";
  }

  function getColumnCellStyle(columnName) {
    const width = getColumnWidth(columnName);
    const baseStyle = {
      width: `${width}px`,
      minWidth: `${width}px`,
      maxWidth: `${width}px`
    };
    if (!pinnedSet.has(columnName)) {
      return baseStyle;
    }
    return {
      ...baseStyle,
      left: `${pinnedLeftMap[columnName] ?? 0}px`
    };
  }

  useEffect(() => {
    const columnsSet = new Set(frameColumns);

    setColumnFilters((prev) => {
      const next = {};
      for (const [column, value] of Object.entries(prev)) {
        if (columnsSet.has(column)) {
          next[column] = value;
        }
      }
      return next;
    });

    setColumnWidths((prev) => {
      const next = {};
      for (const [column, value] of Object.entries(prev)) {
        if (columnsSet.has(column)) {
          next[column] = value;
        }
      }
      return next;
    });

    setPinnedColumns((prev) => prev.filter((column) => columnsSet.has(column)));
    setSortState((prev) =>
      prev.column && !columnsSet.has(prev.column) ? { column: "", direction: "" } : prev
    );
  }, [frameColumns]);

  useEffect(() => {
    if (!isResizingColumn) {
      return undefined;
    }

    const onPointerMove = (event) => {
      const session = resizeSessionRef.current;
      if (!session) {
        return;
      }

      const delta = event.clientX - session.startX;
      const nextWidth = clamp(session.startWidth + delta, MIN_COLUMN_WIDTH, MAX_COLUMN_WIDTH);
      setColumnWidths((prev) => ({ ...prev, [session.columnName]: nextWidth }));
    };

    const onPointerUp = () => {
      resizeSessionRef.current = null;
      setIsResizingColumn(false);
    };

    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    document.body.classList.add("dragging-column-width");

    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      document.body.classList.remove("dragging-column-width");
    };
  }, [isResizingColumn]);

  return {
    viewerField,
    setViewerField,
    viewerKeyword,
    setViewerKeyword,
    columnFilters,
    sortState,
    pinnedColumns,
    displayedRows,
    orderedColumns,
    pinnedSet,
    lastPinnedColumn,
    fieldOptions,
    viewerFieldOptions,
    updateColumnFilter,
    toggleSort,
    togglePinColumn,
    resetColumnFilters,
    resetSort,
    clearPinnedColumns,
    resetViewerSearch,
    resetTableControls,
    handleColumnResizeStart,
    getSortIndicator,
    getColumnCellStyle
  };
}
