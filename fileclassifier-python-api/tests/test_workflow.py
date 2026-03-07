from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from fileclassifier.models import ExecutionOptions, LogicOperator, MatchMode, QueryCondition
from fileclassifier.services.workflow import execute_search


def write_excel_dataset(excel_path: Path) -> None:
    dataframe = pd.DataFrame(
        [
            {"doc_id": "DOC-001", "status": "Approved", "region": "East", "title": "Alpha Package"},
            {"doc_id": "DOC-002", "status": "Approved", "region": "West", "title": "Beta Package"},
            {"doc_id": "DOC-003", "status": "Pending", "region": "North", "title": "Gamma Package"},
            {"doc_id": "DOC-004", "status": "Approved", "region": "East", "title": "Delta Package"},
            {"doc_id": "DOC-005", "status": "Approved", "region": "South", "title": "Epsilon Package"},
        ]
    )
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        dataframe.to_excel(writer, sheet_name="records", index=False)


def create_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("content", encoding="utf-8")


def test_execute_search_reports_expected_stats(tmp_path: Path) -> None:
    excel_path = tmp_path / "records.xlsx"
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    write_excel_dataset(excel_path)
    create_file(input_dir / "DOC-001_alpha.txt")
    create_file(input_dir / "DOC-004_delta_a.pdf")
    create_file(input_dir / "conflicts" / "DOC-004_delta_b.txt")
    create_file(input_dir / "DOC-005_epsilon.md")

    report = execute_search(
        ExecutionOptions(
            excel_path=excel_path,
            sheet_name="records",
            input_dir=input_dir,
            output_dir=output_dir,
            recursive=True,
        ),
        [QueryCondition(field_name="status", match_mode=MatchMode.EXACT, value="Approved")],
        LogicOperator.AND,
    )

    assert report.filtered_records == 4
    assert report.scanned_files == 4
    assert report.matched_records == 3
    assert report.unmatched_records == 1
    assert report.conflict_records == 1
    assert report.matched_files == 4
    assert sorted(path.name for path in report.copied_files) == [
        "DOC-001_alpha.txt",
        "DOC-004_delta_a.pdf",
        "DOC-004_delta_b.txt",
        "DOC-005_epsilon.md",
    ]


def test_non_recursive_scan_skips_nested_matches(tmp_path: Path) -> None:
    excel_path = tmp_path / "records.xlsx"
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    write_excel_dataset(excel_path)
    create_file(input_dir / "nested" / "DOC-003_gamma.txt")

    report = execute_search(
        ExecutionOptions(
            excel_path=excel_path,
            sheet_name="records",
            input_dir=input_dir,
            output_dir=output_dir,
            recursive=False,
        ),
        [QueryCondition(field_name="status", match_mode=MatchMode.EXACT, value="Pending")],
        LogicOperator.AND,
    )

    assert report.filtered_records == 1
    assert report.scanned_files == 0
    assert report.matched_records == 0
    assert report.unmatched_records == 1


def test_execute_search_raises_when_input_path_is_not_directory(tmp_path: Path) -> None:
    excel_path = tmp_path / "records.xlsx"
    input_file = tmp_path / "input.txt"
    output_dir = tmp_path / "output"
    write_excel_dataset(excel_path)
    create_file(input_file)

    with pytest.raises(NotADirectoryError, match="Input path is not a directory"):
        execute_search(
            ExecutionOptions(
                excel_path=excel_path,
                sheet_name="records",
                input_dir=input_file,
                output_dir=output_dir,
                recursive=False,
            ),
            [QueryCondition(field_name="status", match_mode=MatchMode.EXACT, value="Approved")],
            LogicOperator.AND,
        )


def test_execute_search_raises_when_output_path_is_not_directory(tmp_path: Path) -> None:
    excel_path = tmp_path / "records.xlsx"
    input_dir = tmp_path / "input"
    output_file = tmp_path / "output.txt"
    write_excel_dataset(excel_path)
    create_file(input_dir / "DOC-001_alpha.txt")
    create_file(output_file)

    with pytest.raises(NotADirectoryError, match="Output path is not a directory"):
        execute_search(
            ExecutionOptions(
                excel_path=excel_path,
                sheet_name="records",
                input_dir=input_dir,
                output_dir=output_file,
                recursive=False,
            ),
            [QueryCondition(field_name="status", match_mode=MatchMode.EXACT, value="Approved")],
            LogicOperator.AND,
        )
