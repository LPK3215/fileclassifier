export default function AppHeader({ busy, status, theme, onThemeChange, hideStatusChip = false }) {
  return (
    <header className="app-header">
      <div className="brand-block">
        <h1>FileClassifier Web</h1>
        <p>左侧为操作区，右侧为数据预览区。默认 50/50，可拖拽中线调整比例。</p>
      </div>
      <div className="header-controls">
        {!hideStatusChip ? (
          <span className={busy ? "status-chip is-busy" : "status-chip"} aria-live="polite">
            {status}
          </span>
        ) : null}
        <div className="theme-switch" role="group" aria-label="主题切换">
          <button
            type="button"
            className={theme === "light" ? "is-active" : ""}
            onClick={() => onThemeChange("light")}
          >
            浅色
          </button>
          <button
            type="button"
            className={theme === "dark" ? "is-active" : ""}
            onClick={() => onThemeChange("dark")}
          >
            暗色
          </button>
        </div>
      </div>
    </header>
  );
}
