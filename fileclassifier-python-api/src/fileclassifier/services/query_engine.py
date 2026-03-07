from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

import pandas as pd

from fileclassifier.models import LogicOperator, MatchMode, QueryCondition


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value).strip().casefold()
    if not text or text in {"nan", "none", "<na>"}:
        return ""
    return re.sub(r"[\s\-_./\\()]+", "", text)


def fuzzy_score(left: Any, right: Any) -> float:
    normalized_left = normalize_text(left)
    normalized_right = normalize_text(right)
    if not normalized_left or not normalized_right:
        return 0.0
    ratio = SequenceMatcher(None, normalized_left, normalized_right).ratio()
    if normalized_left in normalized_right or normalized_right in normalized_left:
        overlap = min(len(normalized_left), len(normalized_right)) / max(
            len(normalized_left), len(normalized_right)
        )
        ratio = max(ratio, overlap)
    return ratio


def _evaluate_exact(series: pd.Series, value: str) -> pd.Series:
    normalized_value = normalize_text(value)
    return series.apply(lambda item: normalize_text(item) == normalized_value)


def _evaluate_contains(series: pd.Series, value: str) -> pd.Series:
    escaped = re.escape(str(value).strip().casefold())
    prepared = series.fillna("").astype(str).str.casefold()
    return prepared.str.contains(escaped, na=False, regex=True)


def _evaluate_fuzzy(series: pd.Series, value: str) -> pd.Series:
    threshold = 0.72 if len(normalize_text(value)) >= 6 else 0.8
    return series.apply(lambda item: fuzzy_score(value, item) >= threshold)


def _coerce_numeric(value: str) -> float | None:
    if not value:
        return None
    converted = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    return None if pd.isna(converted) else float(converted)


def _coerce_datetime(value: str) -> pd.Timestamp | None:
    if not value:
        return None
    converted = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(converted) else converted


def _evaluate_range(series: pd.Series, start: str, end: str) -> pd.Series:
    numeric_series = pd.to_numeric(series, errors="coerce")
    numeric_start = _coerce_numeric(start)
    numeric_end = _coerce_numeric(end)
    if (numeric_start is not None or numeric_end is not None) and numeric_series.notna().any():
        mask = pd.Series(True, index=series.index)
        if numeric_start is not None:
            mask &= numeric_series >= numeric_start
        if numeric_end is not None:
            mask &= numeric_series <= numeric_end
        return mask.fillna(False)

    datetime_series = pd.to_datetime(series, errors="coerce")
    datetime_start = _coerce_datetime(start)
    datetime_end = _coerce_datetime(end)
    if (datetime_start is not None or datetime_end is not None) and datetime_series.notna().any():
        mask = pd.Series(True, index=series.index)
        if datetime_start is not None:
            mask &= datetime_series >= datetime_start
        if datetime_end is not None:
            mask &= datetime_series <= datetime_end
        return mask.fillna(False)

    prepared = series.fillna("").astype(str).str.strip()
    mask = pd.Series(True, index=series.index)
    if start:
        mask &= prepared >= str(start).strip()
    if end:
        mask &= prepared <= str(end).strip()
    return mask


def evaluate_condition(dataframe: pd.DataFrame, condition: QueryCondition) -> pd.Series:
    series = dataframe[condition.field_name]
    if condition.match_mode == MatchMode.EXACT:
        return _evaluate_exact(series, condition.value).fillna(False)
    if condition.match_mode == MatchMode.CONTAINS:
        return _evaluate_contains(series, condition.value).fillna(False)
    if condition.match_mode == MatchMode.FUZZY:
        return _evaluate_fuzzy(series, condition.value).fillna(False)
    if condition.match_mode == MatchMode.RANGE:
        return _evaluate_range(series, condition.range_start, condition.range_end).fillna(False)
    raise ValueError(f"Unsupported match mode: {condition.match_mode}")


def active_conditions(conditions: list[QueryCondition]) -> list[QueryCondition]:
    return [condition for condition in conditions if condition.is_active]


def apply_filters(
    dataframe: pd.DataFrame,
    conditions: list[QueryCondition],
    logic: LogicOperator,
) -> tuple[pd.DataFrame, pd.Series]:
    usable_conditions = active_conditions(conditions)
    if not usable_conditions:
        mask = pd.Series(True, index=dataframe.index)
        return dataframe.copy(), mask

    masks = [evaluate_condition(dataframe, condition) for condition in usable_conditions]
    final_mask = masks[0].copy()
    for mask in masks[1:]:
        final_mask = final_mask | mask if logic == LogicOperator.OR else final_mask & mask

    final_mask = final_mask.fillna(False)
    return dataframe.loc[final_mask].copy(), final_mask
