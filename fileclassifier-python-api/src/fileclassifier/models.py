from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class LogicOperator(str, Enum):
    AND = "and"
    OR = "or"


class MatchMode(str, Enum):
    EXACT = "exact"
    CONTAINS = "contains"
    FUZZY = "fuzzy"
    RANGE = "range"


@dataclass(slots=True)
class QueryCondition:
    field_name: str
    match_mode: MatchMode
    value: str = ""
    range_start: str = ""
    range_end: str = ""

    @property
    def is_active(self) -> bool:
        if not self.field_name:
            return False

        if self.match_mode == MatchMode.RANGE:
            return bool(self.range_start or self.range_end)

        return bool(self.value)


@dataclass(slots=True)
class ExecutionOptions:
    excel_path: Path
    sheet_name: str
    input_dir: Path
    output_dir: Path
    recursive: bool = False


@dataclass(slots=True)
class ColumnMatchProfile:
    name: str
    score: float
    hit_ratio: float
    uniqueness_ratio: float


@dataclass(slots=True)
class RecordMatch:
    record_number: int
    key_field: str | None
    key_value: str | None
    source_paths: list[Path] = field(default_factory=list)
    copied_paths: list[Path] = field(default_factory=list)

    @property
    def conflict(self) -> bool:
        return len(self.source_paths) > 1

    @property
    def matched(self) -> bool:
        return bool(self.source_paths)


@dataclass(slots=True)
class ExecutionReport:
    scanned_files: int
    filtered_records: int
    matched_records: int
    matched_files: int
    unmatched_records: int
    conflict_records: int
    output_dir: Path
    copied_files: list[Path]
    record_matches: list[RecordMatch]
    log_files: list[Path] = field(default_factory=list)
    selected_columns: list[ColumnMatchProfile] = field(default_factory=list)
