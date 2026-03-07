from __future__ import annotations

from pathlib import Path

import pandas as pd

from fileclassifier.styles import APP_STYLESHEET
from fileclassifier.ui.main_window import MainWindow


def write_excel(path: Path) -> None:
    dataframe = pd.DataFrame(
        {
            "doc_id": ["DOC-001", "DOC-002", "DOC-003"],
            "status": ["Approved", "Pending", "Approved"],
            "client_name": ["Northwind", "Blue River", "Northwind"],
        }
    )
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        dataframe.to_excel(writer, sheet_name="records", index=False)


def test_main_window_splitter_and_viewer_filter(app, tmp_path: Path) -> None:
    assert "combobox-popup: 0;" in APP_STYLESHEET
    assert "QComboBox QAbstractItemView {" in APP_STYLESHEET
    assert "border-radius: 12px;" in APP_STYLESHEET
    assert "QComboBox QAbstractItemView::item:selected {" in APP_STYLESHEET

    excel_path = tmp_path / "sample.xlsx"
    write_excel(excel_path)

    window = MainWindow()
    try:
        window.show()
        app.processEvents()

        assert window.main_splitter.count() == 2
        assert window.left_scroll_area.widgetResizable()
        assert len(window.condition_rows) == 1
        assert window.excel_path_edit.text() == ""
        assert window.sheet_combo.count() == 0
        assert window.sheet_loaded is False
        assert window.viewer_stack.currentIndex() == 0
        assert window.conditions_container.property("flatContainer") is True
        assert window.viewer_filter_inputs_panel.property("flatContainer") is True
        assert window.viewer_filter_actions_panel.property("flatContainer") is True
        assert window.viewer_stack.property("flatContainer") is True
        assert window.choose_excel_button.icon().isNull() is False
        assert window.load_sheet_button.icon().isNull() is False
        assert window.choose_input_button.icon().isNull() is False
        assert window.choose_output_button.icon().isNull() is False
        assert window.viewer_filter_apply_button.icon().isNull() is False
        assert window.viewer_filter_clear_button.icon().isNull() is False
        assert window.add_condition_button.icon().isNull() is False
        assert window.run_button.icon().isNull() is False
        assert window.condition_rows[0].remove_button.icon().isNull() is False
        assert window.results_section.toggle_button.icon().isNull() is False
        assert window.details_section.toggle_button.icon().isNull() is False

        window.excel_path_edit.setText(str(excel_path))
        window.load_excel_metadata(excel_path)
        app.processEvents()

        assert window.sheet_loaded is True
        assert window.viewer_stack.currentIndex() == 1
        assert window.preview_table.rowCount() == 3
        assert window.preview_table.columnCount() == 3
        assert window.preview_table.horizontalHeader().mask().isEmpty() is False

        window.viewer_filter_value_edit.setText("northwind")
        window.apply_viewer_filter()
        app.processEvents()
        assert window.preview_table.rowCount() == 2

        window.clear_viewer_filter()
        app.processEvents()
        assert window.preview_table.rowCount() == 3

        english_index = window.language_combo.findData("en_US")
        window.language_combo.setCurrentIndex(english_index)
        app.processEvents()
        assert "Excel Query-Driven" in window.windowTitle()
        assert window.viewer_card.title_label.text() == "Data Viewer"
        assert window.choose_excel_button.width() >= window.choose_excel_button.sizeHint().width()
        assert window.load_sheet_button.width() >= window.load_sheet_button.sizeHint().width()
        assert (
            window.viewer_filter_apply_button.width()
            >= window.viewer_filter_apply_button.sizeHint().width()
        )
        assert (
            window.viewer_filter_inputs_layout.indexOf(window.viewer_filter_apply_button)
            == -1
        )
        assert (
            window.viewer_filter_actions_layout.indexOf(window.viewer_filter_apply_button)
            >= 0
        )
        assert (
            window.condition_rows[0].remove_button.width()
            >= window.condition_rows[0].remove_button.sizeHint().width()
        )

        initial_visibility = window.details_section.content_widget.isVisible()
        initial_icon_key = window.details_section.toggle_button.icon().cacheKey()
        window.details_section.toggle()
        app.processEvents()
        assert window.details_section.content_widget.isVisible() != initial_visibility
        assert window.details_section.toggle_button.icon().cacheKey() != initial_icon_key
    finally:
        window.close()
