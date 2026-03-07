from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd

from fileclassifier.models import ColumnMatchProfile, RecordMatch
from fileclassifier.services.query_engine import fuzzy_score, normalize_text

COLUMN_HINTS = (
    "id",
    "code",
    "number",
    "no",
    "record",
    "document",
    "invoice",
    "reference",
    "serial",
    "档案",
    "编号",
    "单号",
    "代码",
    "文件号",
    "合同号",
    "报告号",
)

DESCRIPTIVE_HINTS = ("title", "name", "client", "keyword", "描述", "标题", "名称")


@dataclass(slots=True)
class FileEntry:
    path: Path
    normalized_name: str
    stem: str


def scan_files(input_dir: Path, recursive: bool) -> list[Path]:
    iterator = input_dir.rglob("*") if recursive else input_dir.glob("*")
    return sorted(path for path in iterator if path.is_file())


def _normalize_column_name(name: str) -> str:
    return normalize_text(name)


def build_column_profiles(dataframe: pd.DataFrame, files: Sequence[Path]) -> list[ColumnMatchProfile]:
    file_names = [normalize_text(path.stem) for path in files]
    profiles: list[ColumnMatchProfile] = []

    for column in dataframe.columns:
        series = dataframe[column].dropna()
        values = [str(item).strip() for item in series.tolist() if str(item).strip()]
        normalized_values = [normalize_text(item) for item in values if len(normalize_text(item)) >= 3]
        if not normalized_values:
            continue

        unique_values = list(dict.fromkeys(normalized_values))
        sample = unique_values[:50]
        hits = sum(1 for value in sample if any(value in file_name for file_name in file_names))
        hit_ratio = hits / max(len(sample), 1)
        uniqueness_ratio = len(set(normalized_values)) / len(normalized_values)
        digit_ratio = sum(any(character.isdigit() for character in item) for item in sample) / max(
            len(sample), 1
        )
        keyword_score = sum(1 for hint in COLUMN_HINTS if hint in _normalize_column_name(column))
        average_length = sum(len(item) for item in sample) / max(len(sample), 1)
        length_bonus = 0.4 if 4 <= average_length <= 28 else 0.0
        score = (hit_ratio * 5.0) + (uniqueness_ratio * 2.0) + digit_ratio + (keyword_score * 1.4) + length_bonus

        profiles.append(
            ColumnMatchProfile(
                name=str(column),
                score=round(score, 3),
                hit_ratio=round(hit_ratio, 3),
                uniqueness_ratio=round(uniqueness_ratio, 3),
            )
        )

    profiles.sort(key=lambda item: item.score, reverse=True)
    return profiles


def select_candidate_columns(profiles: Sequence[ColumnMatchProfile], limit: int = 3) -> list[ColumnMatchProfile]:
    strong_candidates = [profile for profile in profiles if profile.hit_ratio > 0.0 or profile.score >= 2.5]
    return strong_candidates[:limit] if strong_candidates else list(profiles[:limit])


def _build_file_entries(files: Iterable[Path]) -> list[FileEntry]:
    return [FileEntry(path=path, normalized_name=normalize_text(path.stem), stem=path.stem) for path in files]


def _unique_texts(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        if value and value not in seen:
            items.append(value)
            seen.add(value)
    return items


def build_identifier_variants(value: Any) -> list[str]:
    text = "" if value is None else str(value).strip()
    if not text or text.casefold() in {"nan", "none", "<na>"}:
        return []

    variants: list[str] = []
    normalized = normalize_text(text)
    if len(normalized) >= 3:
        variants.append(normalized)

    for part in re.split(r"[\s,;/_\\\-.()]+", text):
        normalized_part = normalize_text(part)
        if len(normalized_part) >= 4:
            variants.append(normalized_part)

    variants = _unique_texts(variants)
    variants.sort(key=len, reverse=True)
    return variants


def _fallback_texts(row: pd.Series, candidate_columns: Sequence[ColumnMatchProfile]) -> list[str]:
    texts: list[str] = []
    for profile in candidate_columns:
        texts.extend(build_identifier_variants(row.get(profile.name)))
    for column in row.index:
        if any(hint in _normalize_column_name(str(column)) for hint in DESCRIPTIVE_HINTS):
            texts.extend(build_identifier_variants(row.get(column)))
    return _unique_texts(texts)[:8]


def match_record_to_files(
    row: pd.Series,
    record_number: int,
    candidate_columns: Sequence[ColumnMatchProfile],
    files: Sequence[Path],
) -> RecordMatch:
    file_entries = _build_file_entries(files)

    for profile in candidate_columns:
        for variant in build_identifier_variants(row.get(profile.name)):
            direct_hits = [entry.path for entry in file_entries if variant in entry.normalized_name]
            if 0 < len(direct_hits) <= 10:
                return RecordMatch(
                    record_number=record_number,
                    key_field=profile.name,
                    key_value=str(row.get(profile.name)).strip(),
                    source_paths=direct_hits,
                )

    fallback_candidates = _fallback_texts(row, candidate_columns)
    best_score = 0.0
    best_hits: list[Path] = []
    for entry in file_entries:
        score = max((fuzzy_score(candidate, entry.stem) for candidate in fallback_candidates), default=0.0)
        if score > best_score:
            best_score = score
            best_hits = [entry.path]
        elif best_hits and score >= best_score - 0.03:
            best_hits.append(entry.path)

    if best_score >= 0.84 and best_hits:
        key_field = candidate_columns[0].name if candidate_columns else None
        key_value = str(row.get(key_field)).strip() if key_field else None
        return RecordMatch(
            record_number=record_number,
            key_field=key_field,
            key_value=key_value,
            source_paths=best_hits[:5],
        )

    return RecordMatch(record_number=record_number, key_field=None, key_value=None)
