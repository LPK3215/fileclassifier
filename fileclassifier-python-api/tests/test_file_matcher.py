from __future__ import annotations

from pathlib import Path

import pandas as pd

from fileclassifier.services.file_matcher import (
    build_column_profiles,
    match_record_to_files,
    scan_files,
    select_candidate_columns,
)


def create_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("sample", encoding="utf-8")


def test_auto_detects_identifier_column_and_matches_files(tmp_path: Path) -> None:
    dataframe = pd.DataFrame(
        {
            "archive_number": ["ARC-001", "ARC-002"],
            "client_name": ["Northwind", "Blue River"],
            "title": ["Compliance Package", "Pilot Contract"],
        }
    )
    create_file(tmp_path / "ARC-001_contract.txt")
    create_file(tmp_path / "ARC-002_pilot.pdf")
    create_file(tmp_path / "notes.txt")

    files = scan_files(tmp_path, recursive=False)
    profiles = build_column_profiles(dataframe, files)
    selected = select_candidate_columns(profiles)
    record_match = match_record_to_files(dataframe.iloc[0], 2, selected, files)

    assert selected[0].name == "archive_number"
    assert record_match.key_field == "archive_number"
    assert [path.name for path in record_match.source_paths] == ["ARC-001_contract.txt"]


def test_recursive_scan_controls_nested_visibility(tmp_path: Path) -> None:
    create_file(tmp_path / "root" / "DOC-100.txt")
    create_file(tmp_path / "DOC-101.txt")

    non_recursive = scan_files(tmp_path, recursive=False)
    recursive = scan_files(tmp_path, recursive=True)

    assert [path.name for path in non_recursive] == ["DOC-101.txt"]
    assert sorted(path.name for path in recursive) == ["DOC-100.txt", "DOC-101.txt"]
