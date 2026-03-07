from __future__ import annotations

from pathlib import Path

import pandas as pd


class ExcelService:
    @staticmethod
    def list_sheets(excel_path: Path) -> list[str]:
        with pd.ExcelFile(excel_path, engine="openpyxl") as workbook:
            return [str(name) for name in workbook.sheet_names]

    @staticmethod
    def read_sheet(excel_path: Path, sheet_name: str) -> pd.DataFrame:
        dataframe = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")
        dataframe.columns = [str(column).strip() for column in dataframe.columns]
        return dataframe

    @staticmethod
    def preview(dataframe: pd.DataFrame, rows: int = 8) -> pd.DataFrame:
        return dataframe.head(rows).fillna("").astype(str)
