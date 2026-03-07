import FancySelect from "./FancySelect";

export default function Step1ExcelCard({
  excelBaseDir,
  onExcelBaseDirChange,
  busy,
  onPickExcelFile,
  onPickExcelFolder,
  selectedExcelFile,
  onSelectExcelFile,
  excelFileOptions,
  hasExcelFiles,
  onRefreshExcelFiles,
  sheetName,
  onSelectSheet,
  sheetOptions,
  excelPath
}) {
  return (
    <section className="card">
      <h2>Step 1: 加载 Excel</h2>
      <label className="field">
        <span>Excel 目录（可选）</span>
        <input
          value={excelBaseDir}
          onChange={(event) => onExcelBaseDirChange(event.target.value)}
          placeholder="可留空，建议通过“选择文件/文件夹”操作"
        />
      </label>
      <div className="row row-step1">
        <button className="action" onClick={onPickExcelFile} disabled={busy} type="button">
          选择文件
        </button>
        <button className="ghost" onClick={onPickExcelFolder} disabled={busy} type="button">
          选择文件夹
        </button>
        <FancySelect
          value={selectedExcelFile}
          onChange={(nextValue) => {
            void onSelectExcelFile(nextValue);
          }}
          options={excelFileOptions}
          placeholder={hasExcelFiles ? "从默认目录选择 Excel" : "目录中没有 Excel 文件"}
          ariaLabel="从默认目录选择 Excel"
          disabled={busy || !hasExcelFiles}
        />
          <button className="ghost" onClick={onRefreshExcelFiles} disabled={busy} type="button">
            刷新文件列表
          </button>
      </div>
      <p className="hint">选择文件可直接加载；选择文件夹会扫描并在下拉框列出 Excel 文件。</p>
      <label className="field">
        <span>Sheet（切换后自动刷新右侧预览）</span>
        <FancySelect
          value={sheetName}
          onChange={(nextValue) => {
            void onSelectSheet(nextValue);
          }}
          options={sheetOptions}
          placeholder="选择 Sheet"
          ariaLabel="选择 Sheet"
          disabled={busy || !sheetOptions.length}
        />
      </label>
      <p className="hint">当前 Excel: {excelPath || "-"}</p>
    </section>
  );
}
