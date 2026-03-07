from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path

from fileclassifier.models import (
    ExecutionOptions,
    ExecutionReport,
    LogicOperator,
    MatchMode,
    QueryCondition,
)
from fileclassifier.services.excel_service import ExcelService
from fileclassifier.services.file_matcher import (
    build_column_profiles,
    match_record_to_files,
    scan_files,
    select_candidate_columns,
)
from fileclassifier.services.query_engine import active_conditions, apply_filters


def _sanitize_folder_token(raw_text: str, default: str, max_length: int) -> str:
    text = str(raw_text or "").strip()
    if not text:
        return default

    original_text = text
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", text)
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    text = text.strip("._-")
    if not text:
        digest = hashlib.sha1(original_text.encode("utf-8")).hexdigest()[:6]
        return f"{default}-{digest}"

    if len(text) > max_length:
        text = text[:max_length].rstrip("._-")
    return text or default


def _condition_summary_part(condition: QueryCondition) -> str:
    field = _sanitize_folder_token(condition.field_name, "field", max_length=20)

    if condition.match_mode == MatchMode.RANGE:
        start = _sanitize_folder_token(condition.range_start, "min", max_length=14)
        end = _sanitize_folder_token(condition.range_end, "max", max_length=14)
        return f"{field}-range-{start}to{end}"

    mode = condition.match_mode.value
    value = _sanitize_folder_token(condition.value, "any", max_length=24)
    return f"{field}-{mode}-{value}"


def build_run_output_dir(
    base_output_dir: Path,
    conditions: list[QueryCondition],
    logic: LogicOperator,
) -> Path:
    base_output_dir.mkdir(parents=True, exist_ok=True)

    condition_parts = [_condition_summary_part(item) for item in conditions]
    if len(condition_parts) > 3:
        extra_count = len(condition_parts) - 3
        condition_parts = [*condition_parts[:3], f"plus{extra_count}"]
    if not condition_parts:
        condition_parts = ["no-condition"]

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder_name = f"{timestamp}__{logic.value.upper()}__{'__'.join(condition_parts)}"
    folder_name = _sanitize_folder_token(folder_name, default=f"{timestamp}__run", max_length=180)

    candidate = base_output_dir / folder_name
    suffix = 1
    while candidate.exists():
        candidate = base_output_dir / f"{folder_name}__{suffix}"
        suffix += 1

    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def copy_with_unique_name(source_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_path = output_dir / source_path.name
    if not target_path.exists():
        shutil.copy2(source_path, target_path)
        return target_path

    counter = 1
    while True:
        candidate = output_dir / f"{source_path.stem}__{counter}{source_path.suffix}"
        if not candidate.exists():
            shutil.copy2(source_path, candidate)
            return candidate
        counter += 1


def _condition_to_dict(condition: QueryCondition) -> dict[str, str]:
    payload = {
        "field_name": condition.field_name,
        "match_mode": condition.match_mode.value,
    }
    if condition.match_mode == MatchMode.RANGE:
        payload["range_start"] = condition.range_start
        payload["range_end"] = condition.range_end
    else:
        payload["value"] = condition.value
    return payload


def _record_match_status(record_match) -> str:
    if record_match.conflict:
        return "conflict"
    if record_match.matched:
        return "matched"
    return "unmatched"


def save_execution_logs(
    report: ExecutionReport,
    options: ExecutionOptions,
    conditions: list[QueryCondition],
    logic: LogicOperator,
) -> list[Path]:
    report.output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = report.output_dir / "run_summary.txt"
    json_path = report.output_dir / "run_report.json"
    csv_path = report.output_dir / "record_matches.csv"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_lines = [
        f"run_time: {timestamp}",
        f"excel_path: {options.excel_path}",
        f"sheet_name: {options.sheet_name}",
        f"input_dir: {options.input_dir}",
        f"output_dir: {report.output_dir}",
        f"recursive: {options.recursive}",
        f"logic: {logic.value.upper()}",
        "conditions:",
    ]

    if conditions:
        for index, condition in enumerate(conditions, start=1):
            if condition.match_mode == MatchMode.RANGE:
                summary_lines.append(
                    f"  {index}. {condition.field_name} [{condition.match_mode.value}] "
                    f"{condition.range_start or '-'} ~ {condition.range_end or '-'}"
                )
            else:
                summary_lines.append(
                    f"  {index}. {condition.field_name} [{condition.match_mode.value}] {condition.value}"
                )
    else:
        summary_lines.append("  (none)")

    summary_lines.extend(
        [
            "stats:",
            f"  scanned_files: {report.scanned_files}",
            f"  filtered_records: {report.filtered_records}",
            f"  matched_records: {report.matched_records}",
            f"  unmatched_records: {report.unmatched_records}",
            f"  conflict_records: {report.conflict_records}",
            f"  copied_files: {report.matched_files}",
        ]
    )
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    record_items = []
    for item in report.record_matches:
        record_items.append(
            {
                "record_number": item.record_number,
                "key_field": item.key_field,
                "key_value": item.key_value,
                "status": _record_match_status(item),
                "source_paths": [str(path) for path in item.source_paths],
                "copied_paths": [str(path) for path in item.copied_paths],
            }
        )

    payload = {
        "run_time": timestamp,
        "excel_path": str(options.excel_path),
        "sheet_name": options.sheet_name,
        "input_dir": str(options.input_dir),
        "output_dir": str(report.output_dir),
        "recursive": options.recursive,
        "logic": logic.value,
        "conditions": [_condition_to_dict(item) for item in conditions],
        "stats": {
            "scanned_files": report.scanned_files,
            "filtered_records": report.filtered_records,
            "matched_records": report.matched_records,
            "unmatched_records": report.unmatched_records,
            "conflict_records": report.conflict_records,
            "matched_files": report.matched_files,
        },
        "selected_columns": [
            {
                "name": column.name,
                "score": column.score,
                "hit_ratio": column.hit_ratio,
                "uniqueness_ratio": column.uniqueness_ratio,
            }
            for column in report.selected_columns
        ],
        "record_matches": record_items,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=[
                "record_number",
                "key_field",
                "key_value",
                "status",
                "source_paths",
                "copied_paths",
            ],
        )
        writer.writeheader()
        for item in record_items:
            writer.writerow(
                {
                    "record_number": item["record_number"],
                    "key_field": item["key_field"] or "",
                    "key_value": item["key_value"] or "",
                    "status": item["status"],
                    "source_paths": " | ".join(item["source_paths"]),
                    "copied_paths": " | ".join(item["copied_paths"]),
                }
            )

    return [summary_path, json_path, csv_path]


def execute_search(
    options: ExecutionOptions,
    conditions: list[QueryCondition],
    logic: LogicOperator,
) -> ExecutionReport:
    if not options.excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {options.excel_path}")
    if not options.excel_path.is_file():
        raise IsADirectoryError(f"Excel path is not a file: {options.excel_path}")
    if not options.input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {options.input_dir}")
    if not options.input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {options.input_dir}")
    if options.output_dir.exists() and not options.output_dir.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {options.output_dir}")
    if not options.sheet_name:
        raise ValueError("Sheet name is required.")

    validated_conditions = active_conditions(conditions)
    if not validated_conditions:
        raise ValueError("At least one active query condition is required.")
    run_output_dir = build_run_output_dir(options.output_dir, validated_conditions, logic)

    dataframe = ExcelService.read_sheet(options.excel_path, options.sheet_name)
    filtered_dataframe, _ = apply_filters(dataframe, validated_conditions, logic)
    files = scan_files(options.input_dir, options.recursive)

    source_frame = filtered_dataframe if not filtered_dataframe.empty else dataframe.head(0)
    profiles = build_column_profiles(source_frame, files)
    selected_columns = select_candidate_columns(profiles)

    copied_files_by_source: dict[Path, Path] = {}
    record_matches = []

    for row_index, row in filtered_dataframe.iterrows():
        record_number = int(row_index) + 2
        record_match = match_record_to_files(row, record_number, selected_columns, files)
        for source_path in record_match.source_paths:
            copied_path = copied_files_by_source.get(source_path)
            if copied_path is None:
                copied_path = copy_with_unique_name(source_path, run_output_dir)
                copied_files_by_source[source_path] = copied_path
            record_match.copied_paths.append(copied_path)
        record_matches.append(record_match)

    matched_records = sum(match.matched for match in record_matches)
    conflict_records = sum(match.conflict for match in record_matches)
    unmatched_records = max(len(filtered_dataframe) - matched_records, 0)

    report = ExecutionReport(
        scanned_files=len(files),
        filtered_records=len(filtered_dataframe),
        matched_records=matched_records,
        matched_files=len(copied_files_by_source),
        unmatched_records=unmatched_records,
        conflict_records=conflict_records,
        output_dir=run_output_dir,
        copied_files=list(copied_files_by_source.values()),
        record_matches=record_matches,
        selected_columns=selected_columns,
    )
    report.log_files = save_execution_logs(report, options, validated_conditions, logic)
    return report
