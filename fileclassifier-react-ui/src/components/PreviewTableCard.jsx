import FancySelect from "./FancySelect";

export default function PreviewTableCard({
  viewerField,
  onViewerFieldChange,
  viewerFieldOptions,
  viewerKeyword,
  onViewerKeywordChange,
  onClearViewerKeyword,
  onResetColumnFilters,
  onResetSort,
  sortState,
  onClearPinnedColumns,
  pinnedColumns,
  displayedRows,
  totalRows,
  orderedColumns,
  pinnedSet,
  lastPinnedColumn,
  getColumnCellStyle,
  onToggleSort,
  getSortIndicator,
  onTogglePinColumn,
  onColumnResizeStart,
  columnFilters,
  onUpdateColumnFilter
}) {
  return (
    <section className="card preview-card">
      <h2>右侧数据查看区</h2>
      <p className="hint">支持列固定、列宽拖拽、列筛选与排序（点击列名）。</p>
      <div className="row row-viewer">
        <FancySelect
          value={viewerField}
          onChange={onViewerFieldChange}
          options={viewerFieldOptions}
          placeholder="全部字段"
          ariaLabel="选择查看字段"
        />
        <input
          value={viewerKeyword}
          onChange={(event) => onViewerKeywordChange(event.target.value)}
          placeholder="输入关键字"
        />
        <button onClick={onClearViewerKeyword} className="ghost" type="button">
          清空筛选
        </button>
      </div>
      <div className="table-actions">
        <button onClick={onResetColumnFilters} className="ghost" type="button">
          清空列筛选
        </button>
        <button onClick={onResetSort} className="ghost" type="button" disabled={!sortState.column}>
          清空排序
        </button>
        <button
          onClick={onClearPinnedColumns}
          className="ghost"
          type="button"
          disabled={!pinnedColumns.length}
        >
          取消固定列
        </button>
      </div>
      <p className="hint">
        显示 {displayedRows.length} / {totalRows} 行
        {sortState.column ? ` · 排序: ${sortState.column} (${sortState.direction})` : ""}
        {pinnedColumns.length ? ` · 固定列: ${pinnedColumns.length}` : ""}
      </p>
      <div className="table-wrap">
        <table className="preview-table">
          <thead>
            <tr className="preview-header-row">
              {orderedColumns.map((column) => {
                const isPinned = pinnedSet.has(column);
                const isLastPinned = column === lastPinnedColumn;
                const isSorted = sortState.column === column;
                return (
                  <th
                    key={column}
                    className={`preview-col-th${isPinned ? " is-pinned" : ""}${
                      isLastPinned ? " is-pinned-edge" : ""
                    }`}
                    style={getColumnCellStyle(column)}
                    onContextMenu={(event) => {
                      event.preventDefault();
                      onTogglePinColumn(column);
                    }}
                  >
                    <div className="preview-col-head">
                      <button
                        type="button"
                        className={`preview-sort-trigger${isSorted ? " is-active" : ""}`}
                        onClick={() => onToggleSort(column)}
                        title="点击排序，右键列头可快速固定"
                      >
                        <span className="preview-col-name">{column}</span>
                        <span className="preview-sort-indicator">{getSortIndicator(column)}</span>
                      </button>
                      <button
                        type="button"
                        className={`preview-pin-trigger${isPinned ? " is-active" : ""}`}
                        onClick={() => onTogglePinColumn(column)}
                        aria-label={isPinned ? "取消固定列" : "固定到左侧"}
                        title={isPinned ? "取消固定列" : "固定到左侧"}
                      >
                        <span className="sr-only">{isPinned ? "取消固定列" : "固定到左侧"}</span>
                      </button>
                    </div>
                    <button
                      type="button"
                      className="preview-resize-handle"
                      onPointerDown={(event) => onColumnResizeStart(event, column)}
                      aria-label={`拖拽调整 ${column} 列宽`}
                    />
                  </th>
                );
              })}
            </tr>
            <tr className="preview-filter-row">
              {orderedColumns.map((column) => {
                const isPinned = pinnedSet.has(column);
                const isLastPinned = column === lastPinnedColumn;
                return (
                  <th
                    key={`filter_${column}`}
                    className={`preview-col-th is-filter${isPinned ? " is-pinned" : ""}${
                      isLastPinned ? " is-pinned-edge" : ""
                    }`}
                    style={getColumnCellStyle(column)}
                  >
                    <input
                      className="preview-filter-input"
                      value={columnFilters[column] || ""}
                      onChange={(event) => onUpdateColumnFilter(column, event.target.value)}
                      placeholder="筛选"
                    />
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {displayedRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {orderedColumns.map((column) => {
                  const isPinned = pinnedSet.has(column);
                  const isLastPinned = column === lastPinnedColumn;
                  return (
                    <td
                      key={`${rowIndex}_${column}`}
                      className={`preview-col-td${isPinned ? " is-pinned" : ""}${
                        isLastPinned ? " is-pinned-edge" : ""
                      }`}
                      style={getColumnCellStyle(column)}
                      title={row[column] || ""}
                    >
                      {row[column] || ""}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
