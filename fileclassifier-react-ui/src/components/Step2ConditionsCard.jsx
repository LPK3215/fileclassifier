import FancySelect from "./FancySelect";

export default function Step2ConditionsCard({
  logic,
  onLogicChange,
  conditions,
  onUpdateCondition,
  fieldOptions,
  matchModes,
  onOpenRangeEditor,
  onRemoveCondition,
  onAddCondition,
  onApplyConditionPreview,
  busy
}) {
  return (
    <section className="card">
      <div className="section-header">
        <h2>Step 2: 查询条件</h2>
        <div className="logic-toggle">
          <button
            className={logic === "and" ? "selected" : ""}
            onClick={() => onLogicChange("and")}
            type="button"
          >
            AND
          </button>
          <button
            className={logic === "or" ? "selected" : ""}
            onClick={() => onLogicChange("or")}
            type="button"
          >
            OR
          </button>
        </div>
      </div>

      <div className="conditions">
        {conditions.map((condition) => (
          <div className="condition-row" key={condition.id}>
            <FancySelect
              value={condition.field_name}
              onChange={(nextValue) => onUpdateCondition(condition.id, { field_name: nextValue })}
              options={fieldOptions}
              placeholder="字段"
              ariaLabel="选择字段"
            />

            <FancySelect
              value={condition.match_mode}
              onChange={(nextValue) => onUpdateCondition(condition.id, { match_mode: nextValue })}
              options={matchModes}
              placeholder="匹配方式"
              ariaLabel="选择匹配方式"
            />

            {condition.match_mode === "range" ? (
              <button
                type="button"
                className={
                  condition.range_start || condition.range_end
                    ? "range-config-trigger"
                    : "range-config-trigger is-empty"
                }
                onClick={() => onOpenRangeEditor(condition)}
                title="点击配置范围"
              >
                {condition.range_start || condition.range_end
                  ? `${condition.range_start || "起始"} ~ ${condition.range_end || "结束"}`
                  : "点击配置范围"}
              </button>
            ) : (
              <input
                placeholder="值"
                value={condition.value}
                onChange={(event) => onUpdateCondition(condition.id, { value: event.target.value })}
              />
            )}

            <button
              className="ghost"
              onClick={() => onRemoveCondition(condition.id)}
              disabled={conditions.length === 1}
              type="button"
            >
              删除
            </button>
          </div>
        ))}
      </div>
      <div className="row row-two">
        <button onClick={onAddCondition} className="ghost" type="button">
          + 新增条件
        </button>
        <button onClick={onApplyConditionPreview} className="action" disabled={busy} type="button">
          应用条件预览
        </button>
      </div>
    </section>
  );
}
