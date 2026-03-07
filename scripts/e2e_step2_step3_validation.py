from __future__ import annotations

import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


BASE_URL = "http://127.0.0.1:5173"
BACKEND_ROOT = Path("fileclassifier-python-api")
MODE_LABELS = {
    "exact": "精确",
    "contains": "包含",
    "fuzzy": "模糊",
    "range": "范围",
}


@dataclass(slots=True)
class ConditionSpec:
    field: str
    mode: str
    value: str = ""
    range_start: str = ""
    range_end: str = ""


@dataclass(slots=True)
class Scenario:
    name: str
    conditions: list[ConditionSpec]
    logic: str = "and"
    recursive: bool = False
    input_dir: str = "data/input"
    output_dir: str = ""
    apply_preview: bool = True
    expect_success: bool = True
    expected_preview_rows: int | None = None
    expected_stats: dict[str, int] = field(default_factory=dict)
    expected_error_substrings: list[str] = field(default_factory=list)


def card_by_heading(page: Page, heading_text: str):
    return page.locator("section.card").filter(has=page.get_by_role("heading", name=heading_text)).first


def wait_until(predicate, timeout_seconds: float, error_message: str) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.2)
    raise AssertionError(error_message)


def open_select_and_choose(page: Page, trigger, option_label: str) -> None:
    for _ in range(3):
        trigger.click()
        option = page.get_by_role("option", name=option_label).first
        try:
            option.wait_for(state="visible", timeout=5000)
            option.click()
            return
        except Exception:
            page.keyboard.press("Escape")
    raise AssertionError(f"Cannot choose option '{option_label}'.")


def wait_initial_ready(page: Page) -> None:
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    page.wait_for_selector("text=Step 1: 加载 Excel", timeout=90000)

    step3 = card_by_heading(page, "Step 3: 执行复制")
    run_button = step3.get_by_role("button", name="开始执行")
    wait_until(
        lambda: run_button.is_enabled(),
        timeout_seconds=90,
        error_message="Timed out waiting for app to finish initial loading.",
    )

    step1 = card_by_heading(page, "Step 1: 加载 Excel")

    def has_excel_path() -> bool:
        for text in step1.locator("p.hint").all_inner_texts():
            if "当前 Excel:" in text:
                suffix = text.split("当前 Excel:", 1)[1].strip()
                return suffix not in {"", "-"}
        return False

    wait_until(
        has_excel_path,
        timeout_seconds=60,
        error_message="Excel path was not auto-loaded.",
    )


def configure_sheet(page: Page, sheet_name: str) -> None:
    step1 = card_by_heading(page, "Step 1: 加载 Excel")
    trigger = step1.get_by_role("button", name="选择 Sheet")
    open_select_and_choose(page, trigger, sheet_name)


def configure_logic_and_conditions(page: Page, scenario: Scenario) -> None:
    step2 = card_by_heading(page, "Step 2: 查询条件")
    logic_button_name = "AND" if scenario.logic.lower() == "and" else "OR"
    step2.get_by_role("button", name=logic_button_name).click()

    add_button = step2.get_by_role("button", name="+ 新增条件")
    rows = step2.locator(".condition-row")

    while rows.count() < len(scenario.conditions):
        add_button.click()
    while rows.count() > len(scenario.conditions):
        rows.nth(rows.count() - 1).get_by_role("button", name="删除").click()

    for index, condition in enumerate(scenario.conditions):
        row = rows.nth(index)
        open_select_and_choose(page, row.get_by_role("button", name="选择字段"), condition.field)
        mode_label = MODE_LABELS.get(condition.mode)
        if not mode_label:
            raise AssertionError(f"Unsupported mode in scenario '{scenario.name}': {condition.mode}")
        open_select_and_choose(page, row.get_by_role("button", name="选择匹配方式"), mode_label)

        if condition.mode == "range":
            row.locator("button.range-config-trigger").click()
            dialog = page.get_by_role("dialog", name="配置范围")
            dialog.get_by_placeholder("起始值").fill(condition.range_start)
            dialog.get_by_placeholder("结束值").fill(condition.range_end)
            dialog.get_by_role("button", name="保存范围").click()
            dialog.wait_for(state="hidden", timeout=10000)
        else:
            row.get_by_placeholder("值").fill(condition.value)


def configure_execution_options(page: Page, scenario: Scenario) -> None:
    step3 = card_by_heading(page, "Step 3: 执行复制")
    step3.get_by_label("输入目录").fill(scenario.input_dir)
    step3.get_by_label("输出目录").fill(scenario.output_dir)

    recursive_checkbox = step3.get_by_label("递归扫描子目录")
    if scenario.recursive:
        recursive_checkbox.check()
    else:
        recursive_checkbox.uncheck()


def click_and_wait_enabled(button, timeout_seconds: float, timeout_message: str) -> None:
    button.click()
    wait_until(lambda: button.is_enabled(), timeout_seconds=timeout_seconds, error_message=timeout_message)


def parse_preview_rows(page: Page) -> tuple[int, int]:
    preview = card_by_heading(page, "右侧数据查看区")
    for hint in preview.locator("p.hint").all_inner_texts():
        match = re.search(r"显示\s*(\d+)\s*/\s*(\d+)\s*行", hint)
        if match:
            return int(match.group(1)), int(match.group(2))
    raise AssertionError("Cannot read preview rows from right-side viewer.")


def parse_result_stats(page: Page) -> dict[str, int]:
    report = card_by_heading(page, "执行日志与结果")
    report.get_by_role("button", name="结果日志").click()
    report.locator(".stats").wait_for(state="visible", timeout=30000)
    data = report.locator(".stats").evaluate(
        """(el) => {
            const result = {};
            for (const block of el.querySelectorAll("div")) {
                const key = block.querySelector("span")?.textContent?.trim();
                const value = block.querySelector("strong")?.textContent?.trim();
                if (key && value) {
                    result[key] = Number(value);
                }
            }
            return result;
        }"""
    )
    return {str(key): int(value) for key, value in data.items()}


def latest_activity_message(page: Page) -> str:
    report = card_by_heading(page, "执行日志与结果")
    report.get_by_role("button", name="操作日志").click()
    messages = report.locator(".activity-log-message")
    if messages.count() == 0:
        return ""
    return messages.first.inner_text().strip()


def wait_error_message(page: Page, expected_substrings: list[str]) -> str:
    expected_substrings = expected_substrings or ["执行失败"]
    observed = ""
    deadline = time.time() + 30
    while time.time() < deadline:
        status = page.locator(".floating-status").inner_text().strip()
        latest_log = latest_activity_message(page)
        observed = " | ".join(part for part in [status, latest_log] if part)
        if all(fragment in observed for fragment in expected_substrings):
            return observed
        time.sleep(0.2)
    raise AssertionError(
        f"Error text mismatch. Expected fragments={expected_substrings}, observed='{observed}'."
    )


def assert_stats(actual: dict[str, int], expected: dict[str, int], scenario_name: str) -> None:
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if actual_value != expected_value:
            raise AssertionError(
                f"Scenario '{scenario_name}' stat mismatch for '{key}': expected {expected_value}, got {actual_value}."
            )


def run_scenario(page: Page, scenario: Scenario) -> dict[str, object]:
    stage = "wait_initial_ready"
    try:
        wait_initial_ready(page)

        stage = "configure_sheet"
        configure_sheet(page, "records")

        stage = "configure_logic_and_conditions"
        configure_logic_and_conditions(page, scenario)

        stage = "configure_execution_options"
        configure_execution_options(page, scenario)

        if scenario.apply_preview:
            stage = "apply_preview"
            step2 = card_by_heading(page, "Step 2: 查询条件")
            click_and_wait_enabled(
                step2.get_by_role("button", name="应用条件预览"),
                timeout_seconds=60,
                timeout_message=f"Scenario '{scenario.name}' preview timed out.",
            )
            if scenario.expected_preview_rows is not None:
                stage = "validate_preview_rows"
                displayed, total = parse_preview_rows(page)
                if displayed != scenario.expected_preview_rows or total != scenario.expected_preview_rows:
                    raise AssertionError(
                        f"Scenario '{scenario.name}' preview mismatch: displayed={displayed}, total={total},"
                        f" expected={scenario.expected_preview_rows}."
                    )

        stage = "execute_workflow"
        step3 = card_by_heading(page, "Step 3: 执行复制")
        click_and_wait_enabled(
            step3.get_by_role("button", name="开始执行"),
            timeout_seconds=120,
            timeout_message=f"Scenario '{scenario.name}' execute timed out.",
        )

        if scenario.expect_success:
            stage = "parse_result_stats"
            try:
                stats = parse_result_stats(page)
            except Exception as exc:
                status_text = page.locator(".floating-status").inner_text().strip()
                latest_log = latest_activity_message(page)
                raise AssertionError(
                    f"Scenario '{scenario.name}' could not read result stats. "
                    f"status='{status_text}', latest_log='{latest_log}'."
                ) from exc

            stage = "assert_result_stats"
            assert_stats(stats, scenario.expected_stats, scenario.name)
            status_text = page.locator(".floating-status").inner_text().strip()
            if "执行完成" not in status_text and "复制文件" not in status_text:
                raise AssertionError(
                    f"Scenario '{scenario.name}' expected success status but got '{status_text}'."
                )
            return {"stats": stats, "status": status_text}

        stage = "wait_error_message"
        error_text = wait_error_message(page, scenario.expected_error_substrings)
        return {"error": error_text}
    except Exception as exc:
        raise AssertionError(f"Scenario '{scenario.name}' failed at stage '{stage}': {exc}") from exc


def prepare_output_dir(output_path: str) -> None:
    target = Path(output_path)
    if not target.is_absolute():
        target = BACKEND_ROOT / target
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)


def build_scenarios() -> list[Scenario]:
    return [
        Scenario(
            name="exact_single_hit",
            conditions=[ConditionSpec(field="doc_id", mode="exact", value="FC-2025-0001")],
            output_dir=".runtime/e2e_ui/exact_single_hit",
            expected_preview_rows=1,
            expected_stats={"过滤行数": 1, "命中记录": 1, "冲突记录": 0, "复制文件": 1},
        ),
        Scenario(
            name="contains_project_code",
            conditions=[ConditionSpec(field="project_code", mode="contains", value="2507")],
            output_dir=".runtime/e2e_ui/contains_project_code",
            expected_preview_rows=1,
            expected_stats={"过滤行数": 1, "命中记录": 1, "冲突记录": 0, "复制文件": 1},
        ),
        Scenario(
            name="fuzzy_project_code",
            conditions=[ConditionSpec(field="project_code", mode="fuzzy", value="2507-001")],
            output_dir=".runtime/e2e_ui/fuzzy_project_code",
            expected_preview_rows=1,
            expected_stats={"过滤行数": 1, "命中记录": 1, "冲突记录": 0, "复制文件": 1},
        ),
        Scenario(
            name="range_amount_exact_value",
            conditions=[ConditionSpec(field="amount", mode="range", range_start="1337", range_end="1337")],
            output_dir=".runtime/e2e_ui/range_amount_exact_value",
            expected_preview_rows=1,
            expected_stats={"过滤行数": 1, "命中记录": 1, "冲突记录": 0, "复制文件": 1},
        ),
        Scenario(
            name="and_two_doc_ids",
            conditions=[
                ConditionSpec(field="doc_id", mode="exact", value="FC-2025-0001"),
                ConditionSpec(field="doc_id", mode="exact", value="FC-2026-0002"),
            ],
            logic="and",
            output_dir=".runtime/e2e_ui/and_two_doc_ids",
            expected_preview_rows=0,
            expected_stats={"过滤行数": 0, "命中记录": 0, "冲突记录": 0, "复制文件": 0},
        ),
        Scenario(
            name="or_two_doc_ids",
            conditions=[
                ConditionSpec(field="doc_id", mode="exact", value="FC-2025-0001"),
                ConditionSpec(field="doc_id", mode="exact", value="FC-2026-0002"),
            ],
            logic="or",
            output_dir=".runtime/e2e_ui/or_two_doc_ids",
            expected_preview_rows=2,
            expected_stats={"过滤行数": 2, "命中记录": 2, "冲突记录": 0, "复制文件": 2},
        ),
        Scenario(
            name="recursive_off_nested_doc",
            conditions=[ConditionSpec(field="doc_id", mode="exact", value="FC-2026-0176")],
            recursive=False,
            output_dir=".runtime/e2e_ui/recursive_off_nested_doc",
            expected_preview_rows=1,
            expected_stats={"过滤行数": 1, "命中记录": 0, "冲突记录": 0, "复制文件": 0},
        ),
        Scenario(
            name="recursive_on_nested_doc",
            conditions=[ConditionSpec(field="doc_id", mode="exact", value="FC-2026-0176")],
            recursive=True,
            output_dir=".runtime/e2e_ui/recursive_on_nested_doc",
            expected_preview_rows=1,
            expected_stats={"过滤行数": 1, "命中记录": 1, "冲突记录": 0, "复制文件": 1},
        ),
        Scenario(
            name="conflict_doc_recursive",
            conditions=[ConditionSpec(field="doc_id", mode="exact", value="FC-2024-0213")],
            recursive=True,
            output_dir=".runtime/e2e_ui/conflict_doc_recursive",
            expected_preview_rows=1,
            expected_stats={"过滤行数": 1, "命中记录": 1, "冲突记录": 1, "复制文件": 2},
        ),
        Scenario(
            name="no_hit_doc",
            conditions=[ConditionSpec(field="doc_id", mode="exact", value="FC-2099-9999")],
            output_dir=".runtime/e2e_ui/no_hit_doc",
            expected_preview_rows=0,
            expected_stats={"过滤行数": 0, "命中记录": 0, "冲突记录": 0, "复制文件": 0},
        ),
        Scenario(
            name="inactive_condition_error",
            conditions=[ConditionSpec(field="doc_id", mode="exact", value="")],
            apply_preview=False,
            expect_success=False,
            output_dir=".runtime/e2e_ui/inactive_condition_error",
            expected_error_substrings=["执行失败", "At least one active query condition is required"],
        ),
        Scenario(
            name="invalid_input_dir_error",
            conditions=[ConditionSpec(field="doc_id", mode="exact", value="FC-2025-0001")],
            input_dir="data/sample_records.xlsx",
            apply_preview=False,
            expect_success=False,
            output_dir=".runtime/e2e_ui/invalid_input_dir_error",
            expected_error_substrings=["执行失败", "Input path is not a directory"],
        ),
    ]


def main() -> int:
    scenarios = build_scenarios()
    output_root = BACKEND_ROOT / ".runtime" / "e2e_ui"
    output_root.mkdir(parents=True, exist_ok=True)

    failures: list[tuple[str, str, str]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1200})

        for scenario in scenarios:
            prepare_output_dir(scenario.output_dir)
            page = context.new_page()
            try:
                result = run_scenario(page, scenario)
                print(f"[PASS] {scenario.name} -> {result}")
            except Exception as exc:
                screenshot_path = output_root / f"failed_{scenario.name}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                failures.append((scenario.name, str(exc), str(screenshot_path)))
                print(f"[FAIL] {scenario.name} -> {exc}")
            finally:
                page.close()

        context.close()
        browser.close()

    if failures:
        print("\n=== FAILURES ===")
        for name, reason, screenshot in failures:
            print(f"{name}: {reason}")
            print(f"  screenshot: {screenshot}")
        return 1

    print("\nAll Step2/Step3 end-to-end scenarios passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
