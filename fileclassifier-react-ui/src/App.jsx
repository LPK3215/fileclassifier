import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import AppHeader from "./components/AppHeader";
import ExecutionReportCard from "./components/ExecutionReportCard";
import PreviewTableCard from "./components/PreviewTableCard";
import RangeEditorModal from "./components/RangeEditorModal";
import Step1ExcelCard from "./components/Step1ExcelCard";
import Step2ConditionsCard from "./components/Step2ConditionsCard";
import Step3CopyCard from "./components/Step3CopyCard";
import useConditionsState from "./hooks/useConditionsState";
import usePaneSplitter from "./hooks/usePaneSplitter";
import usePreviewTableState from "./hooks/usePreviewTableState";
import { getJson, postJson } from "./lib/api";
import {
  DEFAULT_EXCEL_DIR,
  DEFAULT_INPUT_DIR,
  DEFAULT_OUTPUT_DIR,
  MATCH_MODES,
  MAX_LEFT_RATIO,
  MIN_LEFT_RATIO,
  THEME_STORAGE_KEY,
  getInitialTheme
} from "./lib/ui-helpers";

const EMPTY_FRAME = { columns: [], rows: [], total_rows: 0, returned_rows: 0 };

export default function App() {
  const [excelBaseDir, setExcelBaseDir] = useState(DEFAULT_EXCEL_DIR);
  const [excelFiles, setExcelFiles] = useState([]);
  const [selectedExcelFile, setSelectedExcelFile] = useState("");
  const [excelPath, setExcelPath] = useState("");
  const [sheetNames, setSheetNames] = useState([]);
  const [sheetName, setSheetName] = useState("");
  const [frame, setFrame] = useState(EMPTY_FRAME);
  const [inputDir, setInputDir] = useState(DEFAULT_INPUT_DIR);
  const [outputDir, setOutputDir] = useState(DEFAULT_OUTPUT_DIR);
  const [recursive, setRecursive] = useState(false);
  const [report, setReport] = useState(null);
  const [status, setStatus] = useState("准备就绪");
  const [activityLogs, setActivityLogs] = useState([]);
  const [busy, setBusy] = useState(false);
  const [theme, setTheme] = useState(getInitialTheme);

  const {
    logic,
    setLogic,
    conditions,
    updateCondition,
    addCondition,
    removeCondition,
    sanitizeConditionFields,
    serializeConditions,
    rangeEditor,
    setRangeEditor,
    openRangeEditor,
    closeRangeEditor,
    applyRangeEditor
  } = useConditionsState();

  const {
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
  } = usePreviewTableState({ frameColumns: frame.columns, frameRows: frame.rows });

  const {
    leftPaneRatio,
    isResizing,
    splitRef,
    handleDividerPointerDown,
    handleDividerKeyDown,
    leftPaneBasis,
    rightPaneBasis
  } = usePaneSplitter();
  const leftPaneRef = useRef(null);
  const [rightPaneHeight, setRightPaneHeight] = useState(null);

  const excelFileOptions = useMemo(
    () => excelFiles.map((item) => ({ value: item, label: item })),
    [excelFiles]
  );
  const sheetOptions = useMemo(
    () => sheetNames.map((item) => ({ value: item, label: item })),
    [sheetNames]
  );

  useLayoutEffect(() => {
    const target = leftPaneRef.current;
    if (!target) {
      return undefined;
    }

    const syncHeight = () => {
      const next = Math.ceil(target.getBoundingClientRect().height);
      setRightPaneHeight((prev) => (prev === next ? prev : next));
    };

    syncHeight();

    const observer = new ResizeObserver(() => {
      syncHeight();
    });
    observer.observe(target);
    window.addEventListener("resize", syncHeight);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", syncHeight);
    };
  }, [leftPaneBasis, conditions.length, activityLogs.length, report]);

  function setStatusMessage(message) {
    const normalized = String(message ?? "").trim();
    if (!normalized) {
      return;
    }
    setStatus(normalized);
    const stamp = new Date().toLocaleTimeString("zh-CN", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
    setActivityLogs((prev) => {
      const next = [
        {
          id: `${Date.now()}_${Math.random().toString(16).slice(2)}`,
          time: stamp,
          message: normalized
        },
        ...prev
      ];
      return next.slice(0, 240);
    });
  }

  async function readExcelMetadataAndPreview(pathValue, preferredSheet = "") {
    const normalizedPath = pathValue.trim();
    if (!normalizedPath) {
      throw new Error("请先选择 Excel 文件");
    }

    setStatusMessage("正在读取 Excel 元数据...");
    const metadata = await postJson("/excel/metadata", { excel_path: normalizedPath });
    const availableSheets = metadata.sheet_names || [];
    setSheetNames(availableSheets);

    if (!availableSheets.length) {
      setSheetName("");
      setFrame(EMPTY_FRAME);
      resetViewerSearch();
      resetTableControls();
      setReport(null);
      return { sheetName: "", totalRows: 0 };
    }

    const nextSheet =
      preferredSheet && availableSheets.includes(preferredSheet) ? preferredSheet : availableSheets[0];
    setSheetName(nextSheet);

    setStatusMessage("正在自动加载预览数据...");
    const payload = await postJson("/excel/preview", {
      excel_path: normalizedPath,
      sheet_name: nextSheet,
      max_rows: 240
    });

    setFrame(payload);
    resetViewerSearch();
    setReport(null);
    sanitizeConditionFields(payload.columns);
    return { sheetName: nextSheet, totalRows: payload.total_rows };
  }

  async function loadExcelFromPath(pathValue, preferredSheet = "") {
    const normalizedPath = pathValue.trim();
    if (!normalizedPath) {
      setStatusMessage("请先选择 Excel 文件");
      return;
    }

    setBusy(true);
    setExcelPath(normalizedPath);
    try {
      const result = await readExcelMetadataAndPreview(normalizedPath, preferredSheet);
      if (!result.sheetName) {
        setStatusMessage(`文件已读取，但没有可用 Sheet: ${normalizedPath}`);
        return;
      }
      setStatusMessage(`已自动加载 ${result.sheetName}，共 ${result.totalRows} 行`);
    } catch (error) {
      setStatusMessage(`自动加载失败: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function refreshExcelFiles(baseDirOverride = "") {
    const baseDir = (baseDirOverride || excelBaseDir).trim() || DEFAULT_EXCEL_DIR;
    setBusy(true);
    setStatusMessage(`正在读取目录中的 Excel 文件: ${baseDir}`);
    try {
      const payload = await getJson(`/excel/files?base_dir=${encodeURIComponent(baseDir)}`);
      const files = payload.files || [];
      setExcelBaseDir(payload.base_dir || baseDir);
      setExcelFiles(files);

      if (!files.length) {
        setSelectedExcelFile("");
        setExcelPath("");
        setSheetNames([]);
        setSheetName("");
        setFrame(EMPTY_FRAME);
        resetViewerSearch();
        resetTableControls();
        setReport(null);
        setStatusMessage(`目录中未找到 Excel 文件: ${payload.base_dir}`);
        return;
      }

      const nextPath = files.includes(excelPath) ? excelPath : files[0];
      setSelectedExcelFile(nextPath);
      setExcelPath(nextPath);
      const result = await readExcelMetadataAndPreview(nextPath);
      if (!result.sheetName) {
        setStatusMessage(`已选择 ${nextPath}，但没有可用 Sheet`);
        return;
      }
      setStatusMessage(`已自动加载 ${nextPath} / ${result.sheetName}，共 ${result.totalRows} 行`);
    } catch (error) {
      if (String(error.message) === "Not Found") {
        setStatusMessage("当前后端不支持目录扫描接口，请重启后端后再试。");
        return;
      }
      setStatusMessage(`读取目录失败: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleExcelFileChange(nextPath) {
    setSelectedExcelFile(nextPath);
    if (!nextPath) {
      return;
    }
    await loadExcelFromPath(nextPath);
  }

  async function pickExcelFile() {
    const initialPath = excelBaseDir.trim() || DEFAULT_EXCEL_DIR;
    setBusy(true);
    setStatusMessage("正在打开 Excel 文件选择器...");
    try {
      const payload = await postJson("/system/pick-excel-file", {
        initial_path: initialPath
      });
      if (payload.canceled || !payload.selected_path) {
        setStatusMessage("已取消选择");
        return;
      }
      setSelectedExcelFile("");
      await loadExcelFromPath(payload.selected_path);
    } catch (error) {
      if (String(error.message) === "Not Found") {
        setStatusMessage("当前后端不支持系统文件选择，请重启后端后再试。");
        return;
      }
      setStatusMessage(`选择失败: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function pickExcelFolder() {
    const initialPath = excelBaseDir.trim() || DEFAULT_EXCEL_DIR;
    setBusy(true);
    setStatusMessage("正在打开文件夹选择器...");
    try {
      const payload = await postJson("/system/pick-directory", {
        initial_path: initialPath
      });
      if (payload.canceled || !payload.selected_path) {
        setStatusMessage("已取消选择");
        return;
      }
      await refreshExcelFiles(payload.selected_path);
    } catch (error) {
      if (String(error.message) === "Not Found") {
        setStatusMessage("当前后端不支持系统目录选择，请重启后端后再试。");
        return;
      }
      setStatusMessage(`选择失败: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleSheetChange(nextSheet) {
    setSheetName(nextSheet);
    if (!nextSheet) {
      return;
    }
    if (!excelPath.trim()) {
      setStatusMessage("请先选择 Excel 文件");
      return;
    }

    setBusy(true);
    setStatusMessage(`正在切换 Sheet: ${nextSheet}`);
    try {
      const payload = await postJson("/excel/preview", {
        excel_path: excelPath.trim(),
        sheet_name: nextSheet,
        max_rows: 240
      });
      setFrame(payload);
      resetViewerSearch();
      setReport(null);
      sanitizeConditionFields(payload.columns);
      setStatusMessage(`已切换到 ${nextSheet}，共 ${payload.total_rows} 行`);
    } catch (error) {
      setStatusMessage(`切换 Sheet 失败: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function applyConditionPreview() {
    if (!sheetName) {
      setStatusMessage("请先选择 Sheet");
      return;
    }
    setBusy(true);
    setStatusMessage("正在应用查询条件...");
    try {
      const payload = await postJson("/query/filter-preview", {
        excel_path: excelPath.trim(),
        sheet_name: sheetName,
        logic,
        max_rows: 240,
        conditions: serializeConditions()
      });
      setFrame(payload.frame);
      setStatusMessage(`条件预览完成，命中 ${payload.filtered_rows} 行`);
    } catch (error) {
      setStatusMessage(`条件预览失败: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function pickSystemDirectory(target) {
    const initialPath = target === "input" ? inputDir : outputDir;
    setBusy(true);
    setStatusMessage("正在打开系统目录选择器...");
    try {
      const payload = await postJson("/system/pick-directory", { initial_path: initialPath.trim() });
      if (payload.canceled || !payload.selected_path) {
        setStatusMessage("已取消目录选择");
        return;
      }
      if (target === "input") {
        setInputDir(payload.selected_path);
        setStatusMessage(`已选择输入目录: ${payload.selected_path}`);
      } else {
        setOutputDir(payload.selected_path);
        setStatusMessage(`已选择输出目录: ${payload.selected_path}`);
      }
    } catch (error) {
      if (String(error.message) === "Not Found") {
        setStatusMessage("当前后端不支持系统目录选择，请重启后端后再试。");
        return;
      }
      setStatusMessage(`目录选择失败: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function openOutputDirectory(targetPath = "") {
    const normalizedPath = String(targetPath || outputDir).trim();
    if (!normalizedPath) {
      setStatusMessage("请先设置输出目录");
      return;
    }
    setStatusMessage("正在打开输出目录...");
    try {
      const payload = await postJson("/system/open-folder", { path: normalizedPath });
      setStatusMessage(`已打开输出目录: ${payload.opened_path}`);
    } catch (error) {
      setStatusMessage(`打开输出目录失败: ${error.message}`);
    }
  }

  async function executeWorkflow() {
    if (!inputDir.trim()) {
      setStatusMessage("请先选择输入目录");
      return;
    }
    if (!outputDir.trim()) {
      setStatusMessage("请先选择输出目录");
      return;
    }
    if (!sheetName) {
      setStatusMessage("请先选择 Sheet");
      return;
    }
    setBusy(true);
    setStatusMessage("正在执行匹配与复制...");
    try {
      const payload = await postJson("/workflow/execute", {
        excel_path: excelPath.trim(),
        sheet_name: sheetName,
        input_dir: inputDir.trim(),
        output_dir: outputDir.trim(),
        recursive,
        logic,
        conditions: serializeConditions()
      });
      setReport(payload);
      const runFolderNameParts = String(payload.output_dir || "").split(/[/\\]/).filter(Boolean);
      const runFolderName = runFolderNameParts[runFolderNameParts.length - 1] || "";
      const logFileCount = Array.isArray(payload.log_files) ? payload.log_files.length : 0;
      setStatusMessage(
        runFolderName
          ? `执行完成，复制文件 ${payload.matched_files} 个，目录 ${runFolderName}，日志 ${logFileCount} 个`
          : `执行完成，复制文件 ${payload.matched_files} 个，日志 ${logFileCount} 个`
      );
    } catch (error) {
      setStatusMessage(`执行失败: ${error.message}`);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute("data-theme", theme);
    }
  }, [theme]);

  function getStatusTone() {
    const text = String(status || "").toLowerCase();
    if (busy) {
      return "busy";
    }
    if (
      text.includes("失败") ||
      text.includes("错误") ||
      text.includes("error") ||
      text.includes("not found")
    ) {
      return "error";
    }
    if (text.includes("完成") || text.includes("成功") || text.includes("已")) {
      return "success";
    }
    return "info";
  }

  const showFloatingStatus = busy || status !== "准备就绪";

  return (
    <div className="app-shell" data-theme={theme}>
      <div
        className={`floating-status is-${getStatusTone()}${showFloatingStatus ? " is-visible" : ""}`}
        role="status"
        aria-live="polite"
      >
        {status}
      </div>

      <AppHeader
        busy={busy}
        status={status}
        theme={theme}
        onThemeChange={setTheme}
        hideStatusChip={showFloatingStatus}
      />

      <div className={isResizing ? "workspace is-resizing" : "workspace"} ref={splitRef}>
        <aside
          ref={leftPaneRef}
          className="panel panel-left"
          style={{ flex: `0 0 ${leftPaneBasis}` }}
        >
          <Step1ExcelCard
            excelBaseDir={excelBaseDir}
            onExcelBaseDirChange={setExcelBaseDir}
            busy={busy}
            onPickExcelFile={() => {
              void pickExcelFile();
            }}
            onPickExcelFolder={() => {
              void pickExcelFolder();
            }}
            selectedExcelFile={selectedExcelFile}
            onSelectExcelFile={handleExcelFileChange}
            excelFileOptions={excelFileOptions}
            hasExcelFiles={excelFiles.length > 0}
            onRefreshExcelFiles={() => {
              void refreshExcelFiles();
            }}
            sheetName={sheetName}
            onSelectSheet={handleSheetChange}
            sheetOptions={sheetOptions}
            excelPath={excelPath}
          />

          <Step2ConditionsCard
            logic={logic}
            onLogicChange={setLogic}
            conditions={conditions}
            onUpdateCondition={updateCondition}
            fieldOptions={fieldOptions}
            matchModes={MATCH_MODES}
            onOpenRangeEditor={openRangeEditor}
            onRemoveCondition={removeCondition}
            onAddCondition={addCondition}
            onApplyConditionPreview={() => {
              void applyConditionPreview();
            }}
            busy={busy}
          />

          <Step3CopyCard
            inputDir={inputDir}
            onInputDirChange={setInputDir}
            outputDir={outputDir}
            onOutputDirChange={setOutputDir}
            recursive={recursive}
            onRecursiveChange={setRecursive}
            onPickSystemDirectory={pickSystemDirectory}
            onExecuteWorkflow={() => {
              void executeWorkflow();
            }}
            onOpenOutputDirectory={() => {
              void openOutputDirectory();
            }}
            busy={busy}
            canExecute={Boolean(inputDir.trim() && outputDir.trim() && sheetName)}
          />

          <ExecutionReportCard
            busy={busy}
            outputDir={outputDir}
            runOutputDir={report?.output_dir || ""}
            onOpenOutputDirectory={openOutputDirectory}
            report={report}
            activityLogs={activityLogs}
          />
        </aside>

        <div
          className="splitter"
          role="separator"
          tabIndex={0}
          aria-label="调整左右面板宽度"
          aria-orientation="vertical"
          aria-valuemin={MIN_LEFT_RATIO}
          aria-valuemax={MAX_LEFT_RATIO}
          aria-valuenow={Math.round(leftPaneRatio)}
          onPointerDown={handleDividerPointerDown}
          onKeyDown={handleDividerKeyDown}
        >
          <span />
        </div>

        <main
          className="panel panel-right"
          style={{
            flex: `0 0 ${rightPaneBasis}`,
            height: rightPaneHeight ? `${rightPaneHeight}px` : undefined
          }}
        >
          <PreviewTableCard
            viewerField={viewerField}
            onViewerFieldChange={setViewerField}
            viewerFieldOptions={viewerFieldOptions}
            viewerKeyword={viewerKeyword}
            onViewerKeywordChange={setViewerKeyword}
            onClearViewerKeyword={() => setViewerKeyword("")}
            onResetColumnFilters={resetColumnFilters}
            onResetSort={resetSort}
            sortState={sortState}
            onClearPinnedColumns={clearPinnedColumns}
            pinnedColumns={pinnedColumns}
            displayedRows={displayedRows}
            totalRows={frame.total_rows}
            orderedColumns={orderedColumns}
            pinnedSet={pinnedSet}
            lastPinnedColumn={lastPinnedColumn}
            getColumnCellStyle={getColumnCellStyle}
            onToggleSort={toggleSort}
            getSortIndicator={getSortIndicator}
            onTogglePinColumn={togglePinColumn}
            onColumnResizeStart={handleColumnResizeStart}
            columnFilters={columnFilters}
            onUpdateColumnFilter={updateColumnFilter}
          />
        </main>
      </div>

      <RangeEditorModal
        rangeEditor={rangeEditor}
        setRangeEditor={setRangeEditor}
        onClose={closeRangeEditor}
        onApply={applyRangeEditor}
      />
    </div>
  );
}
