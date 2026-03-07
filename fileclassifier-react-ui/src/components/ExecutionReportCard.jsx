import { useState } from "react";

export default function ExecutionReportCard({
  busy,
  outputDir,
  runOutputDir,
  onOpenOutputDirectory,
  report,
  activityLogs = []
}) {
  const [logView, setLogView] = useState("operations");
  const viewingOperations = logView === "operations";
  const runLogFiles = Array.isArray(report?.log_files) ? report.log_files : [];

  return (
    <section className="card execution-log-card">
      <div className="section-header">
        <h2>执行日志与结果</h2>
        <button
          className="ghost"
          onClick={() => {
            void onOpenOutputDirectory(runOutputDir);
          }}
          disabled={busy || !runOutputDir.trim()}
          type="button"
        >
          打开输出目录
        </button>
      </div>

      <div className="log-output-banner">
        <span className="log-output-label">本次输出目录</span>
        <code className="log-output-path">{runOutputDir || outputDir || "-"}</code>
      </div>
      {runLogFiles.length ? (
        <div className="log-output-banner">
          <span className="log-output-label">已保存日志</span>
          <code className="log-output-path">{runLogFiles.join(" | ")}</code>
        </div>
      ) : null}

      <div className="log-view-toolbar">
        <p className="hint">日志视图</p>
        <div className="log-view-toggle" role="tablist" aria-label="日志视图切换">
          <button
            type="button"
            className={viewingOperations ? "selected" : ""}
            aria-pressed={viewingOperations}
            onClick={() => setLogView("operations")}
          >
            操作日志
          </button>
          <button
            type="button"
            className={!viewingOperations ? "selected" : ""}
            aria-pressed={!viewingOperations}
            onClick={() => setLogView("results")}
          >
            结果日志
          </button>
        </div>
      </div>

      <div className={`log-merged-panel ${viewingOperations ? "is-operations" : "is-results"}`}>
        <p className="hint activity-log-title">
          {viewingOperations ? "操作日志（按钮动作与状态）" : "执行结果（统计与匹配日志）"}
        </p>

        {viewingOperations ? (
          <div className="activity-log-scroll">
            {activityLogs.length ? (
              <ul className="activity-log-list">
                {activityLogs.map((item) => (
                  <li key={item.id}>
                    <span className="activity-log-time">{item.time}</span>
                    <span className="activity-log-message">{item.message}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="placeholder">暂无操作日志</p>
            )}
          </div>
        ) : report ? (
          <>
            <div className="stats">
              <div>
                <span>过滤行数</span>
                <strong>{report.filtered_records}</strong>
              </div>
              <div>
                <span>命中记录</span>
                <strong>{report.matched_records}</strong>
              </div>
              <div>
                <span>冲突记录</span>
                <strong>{report.conflict_records}</strong>
              </div>
              <div>
                <span>复制文件</span>
                <strong>{report.matched_files}</strong>
              </div>
            </div>

            <div className="log-table">
              <table>
                <thead>
                  <tr>
                    <th>Excel 行</th>
                    <th>字段</th>
                    <th>值</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  {report.record_matches.slice(0, 120).map((item) => (
                    <tr key={`${item.record_number}_${item.key_field || "none"}`}>
                      <td>{item.record_number}</td>
                      <td>{item.key_field || "-"}</td>
                      <td>{item.key_value || "-"}</td>
                      <td>
                        <span className={`status status-${item.status}`}>
                          {item.status === "conflict"
                            ? "冲突"
                            : item.status === "matched"
                              ? "命中"
                              : "未命中"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="result-empty-state">
            <p className="placeholder">执行后在这里展示统计和匹配日志</p>
          </div>
        )}
      </div>
    </section>
  );
}
