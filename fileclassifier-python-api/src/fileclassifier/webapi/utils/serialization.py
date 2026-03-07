from __future__ import annotations

from typing import Any

import pandas as pd

from fileclassifier.models import MatchMode, QueryCondition
from fileclassifier.webapi.schemas import FramePayload, QueryConditionPayload


def build_conditions(items: list[QueryConditionPayload]) -> list[QueryCondition]:
    return [
        QueryCondition(
            field_name=item.field_name.strip(),
            match_mode=MatchMode(item.match_mode),
            value=item.value.strip(),
            range_start=item.range_start.strip(),
            range_end=item.range_end.strip(),
        )
        for item in items
    ]


def normalize_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    if pd.isna(value):
        return ""
    return str(value)


def frame_payload(dataframe: pd.DataFrame, max_rows: int) -> FramePayload:
    normalized = dataframe.fillna("")
    normalized.columns = [str(column) for column in normalized.columns]
    preview_rows = normalized.head(max_rows).to_dict(orient="records")
    serialized_rows = [{str(key): normalize_cell(value) for key, value in row.items()} for row in preview_rows]
    return FramePayload(
        columns=[str(column) for column in normalized.columns],
        rows=serialized_rows,
        total_rows=len(normalized),
        returned_rows=len(serialized_rows),
    )

