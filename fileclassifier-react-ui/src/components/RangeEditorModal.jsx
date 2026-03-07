export default function RangeEditorModal({ rangeEditor, setRangeEditor, onClose, onApply }) {
  if (!rangeEditor.open) {
    return null;
  }

  return (
    <div
      className="range-modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className="range-modal"
        role="dialog"
        aria-modal="true"
        aria-label="配置范围"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="range-modal-header">
          <h3>配置范围</h3>
          <button className="ghost" type="button" onClick={onClose}>
            关闭
          </button>
        </div>

        <div className="range-modal-body">
          <label className="field">
            <span>起始</span>
            <input
              value={rangeEditor.rangeStart}
              onChange={(event) =>
                setRangeEditor((prev) => ({ ...prev, rangeStart: event.target.value }))
              }
              placeholder="起始值"
            />
          </label>
          <label className="field">
            <span>结束</span>
            <input
              value={rangeEditor.rangeEnd}
              onChange={(event) =>
                setRangeEditor((prev) => ({ ...prev, rangeEnd: event.target.value }))
              }
              placeholder="结束值"
            />
          </label>
        </div>

        <p className="hint">范围值在弹窗内配置，不会改变查询行布局。</p>

        <div className="range-modal-actions">
          <button
            className="ghost"
            type="button"
            onClick={() => setRangeEditor((prev) => ({ ...prev, rangeStart: "", rangeEnd: "" }))}
          >
            清空
          </button>
          <button className="ghost" type="button" onClick={onClose}>
            取消
          </button>
          <button className="action" type="button" onClick={onApply}>
            保存范围
          </button>
        </div>
      </div>
    </div>
  );
}
