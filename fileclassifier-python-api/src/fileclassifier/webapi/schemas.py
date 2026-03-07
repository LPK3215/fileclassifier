from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MatchModeLiteral = Literal["exact", "contains", "fuzzy", "range"]
LogicLiteral = Literal["and", "or"]


class QueryConditionPayload(BaseModel):
    field_name: str = ""
    match_mode: MatchModeLiteral = "contains"
    value: str = ""
    range_start: str = ""
    range_end: str = ""


class ExcelMetadataRequest(BaseModel):
    excel_path: str


class ExcelMetadataResponse(BaseModel):
    sheet_names: list[str]


class ExcelFileListResponse(BaseModel):
    base_dir: str
    files: list[str]


class ExcelUploadResponse(BaseModel):
    excel_path: str
    filename: str


class DirectoryEntryPayload(BaseModel):
    name: str
    path: str


class DirectoryListResponse(BaseModel):
    current_path: str
    parent_path: str | None
    roots: list[DirectoryEntryPayload]
    directories: list[DirectoryEntryPayload]


class OpenFolderRequest(BaseModel):
    path: str


class OpenFolderResponse(BaseModel):
    opened_path: str


class PickDirectoryRequest(BaseModel):
    initial_path: str = ""


class PickDirectoryResponse(BaseModel):
    selected_path: str | None
    canceled: bool = False


class PickExcelFileRequest(BaseModel):
    initial_path: str = ""


class PickExcelFileResponse(BaseModel):
    selected_path: str | None
    canceled: bool = False


class PickExcelSourceRequest(BaseModel):
    initial_path: str = ""


class PickExcelSourceResponse(BaseModel):
    selected_path: str | None
    source_type: Literal["file", "directory", "none"] = "none"
    canceled: bool = False


class DefaultPathsResponse(BaseModel):
    mode: Literal["desktop", "development"]
    base_dir: str
    excel_base_dir: str
    input_dir: str
    output_dir: str
    logs_dir: str


class PreviewRequest(BaseModel):
    excel_path: str
    sheet_name: str
    max_rows: int = Field(default=240, ge=1, le=2000)


class FilterPreviewRequest(BaseModel):
    excel_path: str
    sheet_name: str
    conditions: list[QueryConditionPayload] = Field(default_factory=list)
    logic: LogicLiteral = "and"
    max_rows: int = Field(default=240, ge=1, le=2000)


class FramePayload(BaseModel):
    columns: list[str]
    rows: list[dict[str, str]]
    total_rows: int
    returned_rows: int


class FilterPreviewResponse(BaseModel):
    frame: FramePayload
    filtered_rows: int


class ColumnMatchProfilePayload(BaseModel):
    name: str
    score: float
    hit_ratio: float
    uniqueness_ratio: float


class RecordMatchPayload(BaseModel):
    record_number: int
    key_field: str | None
    key_value: str | None
    source_paths: list[str]
    copied_paths: list[str]
    status: Literal["matched", "conflict", "unmatched"]


class ExecutionRequest(BaseModel):
    excel_path: str
    sheet_name: str
    input_dir: str
    output_dir: str
    recursive: bool = False
    conditions: list[QueryConditionPayload] = Field(default_factory=list)
    logic: LogicLiteral = "and"


class ExecutionResponse(BaseModel):
    scanned_files: int
    filtered_records: int
    matched_records: int
    matched_files: int
    unmatched_records: int
    conflict_records: int
    output_dir: str
    log_files: list[str] = Field(default_factory=list)
    copied_files: list[str]
    selected_columns: list[ColumnMatchProfilePayload]
    record_matches: list[RecordMatchPayload]
