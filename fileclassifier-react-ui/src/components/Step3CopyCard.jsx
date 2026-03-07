export default function Step3CopyCard({
  inputDir,
  onInputDirChange,
  outputDir,
  onOutputDirChange,
  recursive,
  onRecursiveChange,
  onPickSystemDirectory,
  onExecuteWorkflow,
  onOpenOutputDirectory,
  busy,
  canExecute
}) {
  return (
    <section className="card">
      <h2>Step 3: 执行复制</h2>
      <label className="field">
        <span>输入目录</span>
        <div className="path-input-group">
          <input value={inputDir} onChange={(event) => onInputDirChange(event.target.value)} />
          <button
            className="ghost"
            type="button"
            onClick={() => {
              void onPickSystemDirectory("input");
            }}
            disabled={busy}
          >
            选择目录
          </button>
        </div>
      </label>
      <label className="field">
        <span>输出目录</span>
        <div className="path-input-group">
          <input value={outputDir} onChange={(event) => onOutputDirChange(event.target.value)} />
          <button
            className="ghost"
            type="button"
            onClick={() => {
              void onPickSystemDirectory("output");
            }}
            disabled={busy}
          >
            选择目录
          </button>
        </div>
      </label>
      <label className="checkbox">
        <input checked={recursive} onChange={(event) => onRecursiveChange(event.target.checked)} type="checkbox" />
        递归扫描子目录
      </label>
      <p className="hint">
        每次执行会在输出目录下自动创建“按筛选条件命名”的子文件夹，并自动保存运行日志文件。
      </p>
      <div className="row row-two">
        <button className="action" onClick={onExecuteWorkflow} disabled={busy || !canExecute} type="button">
          开始执行
        </button>
        <button
          className="ghost"
          onClick={onOpenOutputDirectory}
          disabled={busy || !outputDir.trim()}
          type="button"
        >
          打开输出目录
        </button>
      </div>
    </section>
  );
}
