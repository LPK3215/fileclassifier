from __future__ import annotations

import pandas as pd

from fileclassifier.models import LogicOperator, MatchMode, QueryCondition
from fileclassifier.services.query_engine import apply_filters


def build_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "status": ["Approved", "Pending", "Archived", "Approved"],
            "title": [
                "Compliance Package",
                "Pilot Contract",
                "Complaince Package",
                "Quarterly Memo",
            ],
            "amount": [1500, 3200, 4600, 2800],
            "region": ["East", "West", "East", "North"],
        }
    )


def test_exact_match_filters_single_condition() -> None:
    dataframe = build_dataframe()
    filtered, _ = apply_filters(
        dataframe,
        [QueryCondition(field_name="status", match_mode=MatchMode.EXACT, value="Approved")],
        LogicOperator.AND,
    )
    assert filtered["title"].tolist() == ["Compliance Package", "Quarterly Memo"]


def test_contains_match_filters_case_insensitive() -> None:
    dataframe = build_dataframe()
    filtered, _ = apply_filters(
        dataframe,
        [QueryCondition(field_name="title", match_mode=MatchMode.CONTAINS, value="pilot")],
        LogicOperator.AND,
    )
    assert filtered["status"].tolist() == ["Pending"]


def test_fuzzy_match_catches_small_typos() -> None:
    dataframe = build_dataframe()
    filtered, _ = apply_filters(
        dataframe,
        [QueryCondition(field_name="title", match_mode=MatchMode.FUZZY, value="Compliance Packge")],
        LogicOperator.AND,
    )
    assert set(filtered["title"].tolist()) == {"Compliance Package", "Complaince Package"}


def test_range_match_filters_numeric_values() -> None:
    dataframe = build_dataframe()
    filtered, _ = apply_filters(
        dataframe,
        [
            QueryCondition(
                field_name="amount",
                match_mode=MatchMode.RANGE,
                range_start="2000",
                range_end="4000",
            )
        ],
        LogicOperator.AND,
    )
    assert filtered["title"].tolist() == ["Pilot Contract", "Quarterly Memo"]


def test_and_or_logic_combine_multiple_conditions() -> None:
    dataframe = build_dataframe()
    conditions = [
        QueryCondition(field_name="status", match_mode=MatchMode.EXACT, value="Approved"),
        QueryCondition(field_name="region", match_mode=MatchMode.EXACT, value="East"),
    ]
    filtered_and, _ = apply_filters(dataframe, conditions, LogicOperator.AND)
    filtered_or, _ = apply_filters(dataframe, conditions, LogicOperator.OR)

    assert filtered_and["title"].tolist() == ["Compliance Package"]
    assert set(filtered_or["title"].tolist()) == {
        "Compliance Package",
        "Complaince Package",
        "Quarterly Memo",
    }


def test_non_range_condition_with_stale_range_values_is_ignored() -> None:
    dataframe = build_dataframe()
    filtered, _ = apply_filters(
        dataframe,
        [
            QueryCondition(
                field_name="status",
                match_mode=MatchMode.EXACT,
                value="",
                range_start="A",
                range_end="Z",
            )
        ],
        LogicOperator.AND,
    )
    assert len(filtered) == len(dataframe)


def test_range_condition_with_stale_value_is_ignored_without_boundaries() -> None:
    dataframe = build_dataframe()
    filtered, _ = apply_filters(
        dataframe,
        [
            QueryCondition(
                field_name="amount",
                match_mode=MatchMode.RANGE,
                value="legacy-hidden-value",
                range_start="",
                range_end="",
            )
        ],
        LogicOperator.AND,
    )
    assert len(filtered) == len(dataframe)
