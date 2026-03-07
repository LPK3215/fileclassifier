from __future__ import annotations

from pathlib import Path

import pandas as pd

from fileclassifier.services.mock_data import generate_mock_dataset


def _has_cjk_and_latin(value: str) -> bool:
    has_cjk = any("\u4e00" <= char <= "\u9fff" for char in value)
    has_latin = any(char.isascii() and char.isalpha() for char in value)
    return has_cjk and has_latin


def test_generate_mock_dataset_uses_mixed_language_content(tmp_path: Path) -> None:
    manifest = generate_mock_dataset(tmp_path, record_total=24)

    excel_path = manifest["excel_path"]
    input_dir = manifest["input_dir"]

    dataframe = pd.read_excel(excel_path, sheet_name="records")
    visible_columns = set(dataframe.columns.tolist())

    assert "client_slug" not in visible_columns
    assert "category_slug" not in visible_columns
    assert "keyword_slug" not in visible_columns

    assert dataframe["client_name"].map(_has_cjk_and_latin).any()
    assert dataframe["keyword"].map(_has_cjk_and_latin).any()
    assert dataframe["title"].map(_has_cjk_and_latin).any()
    assert dataframe["owner"].map(_has_cjk_and_latin).any()

    sample_text_file = next(input_dir.glob("*.txt"))
    text_content = sample_text_file.read_text(encoding="utf-8")
    assert _has_cjk_and_latin(text_content)
