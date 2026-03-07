from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtCore import QObject, QSize, QThread, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from fileclassifier.icons import icon_path, load_icon
from fileclassifier.i18n import LanguageManager, SUPPORTED_LANGUAGES
from fileclassifier.models import ExecutionOptions, ExecutionReport, LogicOperator
from fileclassifier.services.excel_service import ExcelService
from fileclassifier.services.workflow import execute_search
from fileclassifier.styles import build_app_stylesheet
from fileclassifier.ui.widgets import (
    CardFrame,
    CollapsibleSection,
    ConditionRow,
    MetricCard,
    RoundedComboBox,
    RoundedScrollArea,
    RoundedSplitter,
    RoundedTableWidget,
)


class ExecutionWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, options: ExecutionOptions, conditions: list, logic: LogicOperator) -> None:
        super().__init__()
        self.options = options
        self.conditions = conditions
        self.logic = logic

    def run(self) -> None:
        try:
            report = execute_search(self.options, self.conditions, self.logic)
        except Exception as exc:  # pragma: no cover - surfaced through UI
            self.failed.emit(str(exc))
        else:
            self.finished.emit(report)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.language_manager = LanguageManager("zh_CN")
        self.logic_operator = LogicOperator.AND
        self.current_dataframe = pd.DataFrame()
        self.current_sheet_names: list[str] = []
        self.condition_rows: list[ConditionRow] = []
        self.sheet_loaded = False
        self._status_key = "run.idle"
        self._worker_thread: QThread | None = None
        self._worker: ExecutionWorker | None = None
        self._initial_splitter_applied = False
        self.project_root = Path(__file__).resolve().parents[3]
        self.dropdown_icon_path = icon_path("dropdown")
        self.app_icon_path = icon_path("app")

        self.resize(1320, 820)
        self.setMinimumSize(1080, 720)
        self.setStyleSheet(build_app_stylesheet(self.dropdown_icon_path))
        self._apply_window_icon()
        self._build_ui()
        self._bind_events()
        self.add_condition_row()
        self.retranslate_ui()
        self._show_viewer_placeholder()

    def _apply_window_icon(self) -> None:
        icon = QIcon(str(self.app_icon_path))
        if icon.isNull():
            return
        self.setWindowIcon(icon)
        app = QApplication.instance()
        if app is not None:
            app.setWindowIcon(icon)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if self._initial_splitter_applied:
            return
        total_width = self.main_splitter.size().width()
        if total_width > 0:
            left_width = total_width // 2
            self.main_splitter.setSizes([left_width, total_width - left_width])
            self._initial_splitter_applied = True

    def _build_ui(self) -> None:
        central = QWidget()
        central.setProperty("flatContainer", True)
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(18, 18, 18, 18)
        central_layout.setSpacing(0)
        self.setCentralWidget(central)

        self.main_splitter = RoundedSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("MainSplitter")
        self.main_splitter.setChildrenCollapsible(False)
        central_layout.addWidget(self.main_splitter)

        self.left_scroll_area = RoundedScrollArea()
        self.left_scroll_area.setWidgetResizable(True)
        self.left_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.left_scroll_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self.left_container = QWidget()
        self.left_container.setProperty("flatContainer", True)
        self.left_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.left_layout = QVBoxLayout(self.left_container)
        self.left_layout.setContentsMargins(0, 0, 18, 0)
        self.left_layout.setSpacing(18)
        self.left_scroll_area.setWidget(self.left_container)
        self.main_splitter.addWidget(self.left_scroll_area)

        self.viewer_card = CardFrame()
        self.viewer_card.setProperty("viewerPanel", True)
        self.main_splitter.addWidget(self.viewer_card)
        self.main_splitter.setSizes([1000, 980])
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)

        self.hero_frame = QFrame()
        self.hero_frame.setObjectName("CardFrame")
        self.hero_frame.setProperty("card", True)
        self.hero_frame.setProperty("heroCard", True)
        hero_layout = QHBoxLayout(self.hero_frame)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(18)

        hero_text_layout = QVBoxLayout()
        hero_text_layout.setSpacing(8)
        self.hero_title = QLabel()
        self.hero_title.setObjectName("HeroTitle")
        self.hero_subtitle = QLabel()
        self.hero_subtitle.setObjectName("HeroSubtitle")
        self.hero_subtitle.setWordWrap(True)
        hero_text_layout.addWidget(self.hero_title)
        hero_text_layout.addWidget(self.hero_subtitle)

        lang_layout = QVBoxLayout()
        lang_layout.setContentsMargins(0, 12, 0, 0)
        lang_layout.setSpacing(0)
        self.language_combo = RoundedComboBox()
        self.language_combo.setMinimumWidth(148)
        for language_code, _ in SUPPORTED_LANGUAGES:
            self.language_combo.addItem(language_code, language_code)
        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch(1)

        hero_layout.addLayout(hero_text_layout, 1)
        hero_layout.addLayout(lang_layout)
        self.left_layout.addWidget(self.hero_frame)

        self.step1_card = CardFrame()
        self.step1_card.setProperty("stepCard", True)
        self.step2_card = CardFrame()
        self.step2_card.setProperty("stepCard", True)
        self.step3_card = CardFrame()
        self.step3_card.setProperty("stepCard", True)
        self.results_section = CollapsibleSection()
        self.results_section.setProperty("supportCard", True)
        self.details_section = CollapsibleSection()
        self.details_section.setProperty("supportCard", True)
        self.viewer_card.title_label.setProperty("panelTitle", True)
        self.results_section.title_label.setProperty("panelTitle", True)
        self.details_section.title_label.setProperty("panelTitle", True)
        self.left_layout.addWidget(self.step1_card)
        self.left_layout.addWidget(self.step2_card)
        self.left_layout.addWidget(self.step3_card)
        self.left_layout.addWidget(self.results_section)
        self.left_layout.addWidget(self.details_section)
        self.left_layout.addStretch(1)

        self._build_step1()
        self._build_step2()
        self._build_step3()
        self._build_results()
        self._build_details()
        self._build_viewer()
        self._apply_icons()
        self.details_section.toggle()

    def _build_step1(self) -> None:
        self.excel_label = QLabel()
        self.excel_label.setObjectName("SectionLabel")
        self.excel_path_edit = QLineEdit()
        self.excel_path_edit.setReadOnly(True)
        self.excel_path_edit.setClearButtonEnabled(False)
        self.choose_excel_button = QPushButton()
        self.choose_excel_button.setProperty("secondary", True)

        excel_row = QHBoxLayout()
        excel_row.addWidget(self.excel_label)
        excel_row.addWidget(self.excel_path_edit, 1)
        excel_row.addWidget(self.choose_excel_button)
        self.step1_card.body_layout.addLayout(excel_row)

        self.sheet_label = QLabel()
        self.sheet_label.setObjectName("SectionLabel")
        self.sheet_combo = RoundedComboBox()
        self.load_sheet_button = QPushButton()
        self.load_sheet_button.setProperty("secondary", True)

        sheet_row = QHBoxLayout()
        sheet_row.addWidget(self.sheet_label)
        sheet_row.addWidget(self.sheet_combo, 1)
        sheet_row.addWidget(self.load_sheet_button)
        self.step1_card.body_layout.addLayout(sheet_row)

        self.summary_label = QLabel()
        self.summary_label.setObjectName("SectionLabel")
        self.summary_value = QLabel()
        self.summary_value.setObjectName("BodyText")
        self.summary_value.setWordWrap(True)
        self.step1_card.body_layout.addWidget(self.summary_label)
        self.step1_card.body_layout.addWidget(self.summary_value)

    def _build_step2(self) -> None:
        logic_row = QHBoxLayout()
        self.logic_label = QLabel()
        self.logic_label.setObjectName("SectionLabel")
        self.logic_and_button = QPushButton()
        self.logic_and_button.setCheckable(True)
        self.logic_and_button.setProperty("logic", True)
        self.logic_or_button = QPushButton()
        self.logic_or_button.setCheckable(True)
        self.logic_or_button.setProperty("logic", True)

        logic_row.addWidget(self.logic_label)
        logic_row.addStretch(1)
        logic_row.addWidget(self.logic_and_button)
        logic_row.addWidget(self.logic_or_button)
        self.step2_card.body_layout.addLayout(logic_row)

        self.auto_match_hint = QLabel()
        self.auto_match_hint.setObjectName("BodyText")
        self.auto_match_hint.setWordWrap(True)
        self.step2_card.body_layout.addWidget(self.auto_match_hint)

        self.conditions_container = QWidget()
        self.conditions_container.setProperty("flatContainer", True)
        self.conditions_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.conditions_layout = QVBoxLayout(self.conditions_container)
        self.conditions_layout.setContentsMargins(0, 0, 0, 0)
        self.conditions_layout.setSpacing(12)
        self.step2_card.body_layout.addWidget(self.conditions_container)

        add_row = QHBoxLayout()
        add_row.addStretch(1)
        self.add_condition_button = QPushButton()
        self.add_condition_button.setProperty("secondary", True)
        add_row.addWidget(self.add_condition_button)
        self.step2_card.body_layout.addLayout(add_row)

    def _build_step3(self) -> None:
        self.input_label = QLabel()
        self.input_label.setObjectName("SectionLabel")
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setReadOnly(True)
        self.input_path_edit.setClearButtonEnabled(False)
        self.choose_input_button = QPushButton()
        self.choose_input_button.setProperty("secondary", True)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input_label)
        input_row.addWidget(self.input_path_edit, 1)
        input_row.addWidget(self.choose_input_button)
        self.step3_card.body_layout.addLayout(input_row)

        self.output_label = QLabel()
        self.output_label.setObjectName("SectionLabel")
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setClearButtonEnabled(False)
        self.choose_output_button = QPushButton()
        self.choose_output_button.setProperty("secondary", True)

        output_row = QHBoxLayout()
        output_row.addWidget(self.output_label)
        output_row.addWidget(self.output_path_edit, 1)
        output_row.addWidget(self.choose_output_button)
        self.step3_card.body_layout.addLayout(output_row)

        run_row = QHBoxLayout()
        self.recursive_checkbox = QCheckBox()
        self.run_button = QPushButton()
        self.run_button.setProperty("primary", True)
        self.run_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.run_button.setMinimumWidth(190)
        self.status_label = QLabel()
        self.status_label.setObjectName("StatusText")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("InlineProgress")
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(180)

        run_row.addWidget(self.recursive_checkbox)
        run_row.addStretch(1)
        run_row.addWidget(self.status_label)
        run_row.addWidget(self.progress_bar)
        run_row.addWidget(self.run_button)
        self.step3_card.body_layout.addLayout(run_row)

    def _build_results(self) -> None:
        metrics_layout = QGridLayout()
        metrics_layout.setHorizontalSpacing(12)
        metrics_layout.setVerticalSpacing(12)
        self.metric_cards = {
            "scanned": MetricCard(""),
            "matched_files": MetricCard(""),
            "unmatched": MetricCard(""),
            "conflicts": MetricCard(""),
            "filtered": MetricCard(""),
            "matched_records": MetricCard(""),
        }
        positions = [
            ("scanned", 0, 0),
            ("matched_files", 0, 1),
            ("unmatched", 1, 0),
            ("conflicts", 1, 1),
            ("filtered", 2, 0),
            ("matched_records", 2, 1),
        ]
        for key, row, column in positions:
            metrics_layout.addWidget(self.metric_cards[key], row, column)
        self.results_section.content_layout.addLayout(metrics_layout)

        self.results_table = RoundedTableWidget(0, 5)
        self.results_table.setProperty("dataGrid", True)
        self.results_table.setMinimumHeight(240)
        self.results_table.setFrameShape(QFrame.Shape.NoFrame)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.verticalHeader().setVisible(False)
        if hasattr(self.results_table, "setCornerButtonEnabled"):
            self.results_table.setCornerButtonEnabled(False)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.results_table_shell = QFrame()
        self.results_table_shell.setProperty("tableShell", True)
        self.results_table_shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        results_table_layout = QVBoxLayout(self.results_table_shell)
        results_table_layout.setContentsMargins(10, 10, 10, 10)
        results_table_layout.setSpacing(10)

        self.auto_columns_strip = QFrame()
        self.auto_columns_strip.setProperty("softStrip", True)
        self.auto_columns_strip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        auto_columns_row = QHBoxLayout(self.auto_columns_strip)
        auto_columns_row.setContentsMargins(12, 10, 12, 10)
        auto_columns_row.setSpacing(8)
        self.auto_columns_label = QLabel()
        self.auto_columns_label.setObjectName("SectionLabel")
        self.auto_columns_value = QLabel()
        self.auto_columns_value.setObjectName("BodyText")
        self.auto_columns_value.setWordWrap(True)
        auto_columns_row.addWidget(self.auto_columns_label)
        auto_columns_row.addWidget(self.auto_columns_value, 1)
        results_table_layout.addWidget(self.auto_columns_strip)

        results_table_layout.addWidget(self.results_table)
        self.results_section.content_layout.addWidget(self.results_table_shell)

    def _build_details(self) -> None:
        self.details_body = QLabel()
        self.details_body.setWordWrap(True)
        self.details_body.setObjectName("BodyText")
        self.details_section.content_layout.addWidget(self.details_body)

    def _build_viewer(self) -> None:
        filter_header_row = QHBoxLayout()
        filter_header_row.setContentsMargins(0, 0, 0, 0)
        filter_header_row.setSpacing(10)
        self.viewer_filter_label = QLabel()
        self.viewer_filter_label.setObjectName("SectionLabel")
        filter_header_row.addWidget(self.viewer_filter_label)
        filter_header_row.addStretch(1)
        self.viewer_card.body_layout.addLayout(filter_header_row)

        self.viewer_filter_inputs_panel = QWidget()
        self.viewer_filter_inputs_panel.setProperty("flatContainer", True)
        self.viewer_filter_inputs_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.viewer_filter_inputs_layout = QHBoxLayout(self.viewer_filter_inputs_panel)
        self.viewer_filter_inputs_layout.setContentsMargins(0, 0, 0, 0)
        self.viewer_filter_inputs_layout.setSpacing(12)
        self.viewer_filter_column_combo = RoundedComboBox()
        self.viewer_filter_column_combo.setMinimumWidth(168)
        self.viewer_filter_column_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.viewer_filter_value_edit = QLineEdit()
        self.viewer_filter_value_edit.setClearButtonEnabled(True)
        self.viewer_filter_value_edit.setMinimumWidth(138)
        self.viewer_filter_value_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.viewer_filter_inputs_layout.addWidget(self.viewer_filter_column_combo, 2)
        self.viewer_filter_inputs_layout.addWidget(self.viewer_filter_value_edit, 3)
        self.viewer_card.body_layout.addWidget(self.viewer_filter_inputs_panel)

        self.viewer_filter_actions_panel = QWidget()
        self.viewer_filter_actions_panel.setProperty("flatContainer", True)
        self.viewer_filter_actions_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.viewer_filter_actions_layout = QHBoxLayout(self.viewer_filter_actions_panel)
        self.viewer_filter_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.viewer_filter_actions_layout.setSpacing(12)
        self.viewer_rows_label = QLabel()
        self.viewer_rows_label.setObjectName("MutedText")
        self.viewer_filter_apply_button = QPushButton()
        self.viewer_filter_apply_button.setProperty("secondary", True)
        self.viewer_filter_clear_button = QPushButton()
        self.viewer_filter_clear_button.setProperty("ghost", True)
        self.viewer_filter_actions_layout.addWidget(self.viewer_rows_label)
        self.viewer_filter_actions_layout.addStretch(1)
        self.viewer_filter_actions_layout.addWidget(self.viewer_filter_apply_button)
        self.viewer_filter_actions_layout.addWidget(self.viewer_filter_clear_button)
        self.viewer_card.body_layout.addWidget(self.viewer_filter_actions_panel)

        self.viewer_content_shell = QFrame()
        self.viewer_content_shell.setProperty("tableShell", True)
        self.viewer_content_shell.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        viewer_content_layout = QVBoxLayout(self.viewer_content_shell)
        viewer_content_layout.setContentsMargins(6, 6, 6, 6)
        viewer_content_layout.setSpacing(0)

        self.viewer_stack = QStackedWidget()
        self.viewer_stack.setProperty("flatContainer", True)
        self.viewer_stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.viewer_placeholder = QLabel()
        self.viewer_placeholder.setObjectName("ViewerPlaceholder")
        self.viewer_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.viewer_placeholder.setWordWrap(True)
        self.viewer_stack.addWidget(self.viewer_placeholder)

        table_page = QWidget()
        table_page.setProperty("flatContainer", True)
        table_page.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        table_layout = QVBoxLayout(table_page)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        self.preview_table = RoundedTableWidget(0, 0)
        self.preview_table.setProperty("dataGrid", True)
        self.preview_table.setSortingEnabled(True)
        self.preview_table.setFrameShape(QFrame.Shape.NoFrame)
        self.preview_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.verticalHeader().setVisible(False)
        if hasattr(self.preview_table, "setCornerButtonEnabled"):
            self.preview_table.setCornerButtonEnabled(False)
        self.preview_table.horizontalHeader().setSectionsClickable(True)
        self.preview_table.horizontalHeader().setSortIndicatorShown(True)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.preview_table.horizontalHeader().setStretchLastSection(False)
        table_layout.addWidget(self.preview_table)
        self.viewer_stack.addWidget(table_page)

        viewer_content_layout.addWidget(self.viewer_stack)
        self.viewer_card.body_layout.addWidget(self.viewer_content_shell, 1)

    def _apply_icons(self) -> None:
        action_icons = {
            self.choose_excel_button: "choose_excel",
            self.load_sheet_button: "load_sheet",
            self.choose_input_button: "choose_input",
            self.choose_output_button: "choose_output",
            self.add_condition_button: "add_condition",
            self.run_button: "run",
            self.viewer_filter_apply_button: "apply_filter",
            self.viewer_filter_clear_button: "clear_filter",
        }
        for button, icon_name in action_icons.items():
            button.setIcon(load_icon(icon_name))
            button.setIconSize(QSize(18, 18))

    def _bind_events(self) -> None:
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        self.choose_excel_button.clicked.connect(self.choose_excel_file)
        self.load_sheet_button.clicked.connect(self.load_selected_sheet)
        self.sheet_combo.currentIndexChanged.connect(self.load_selected_sheet)
        self.choose_input_button.clicked.connect(lambda: self.choose_directory(self.input_path_edit))
        self.choose_output_button.clicked.connect(lambda: self.choose_directory(self.output_path_edit))
        self.add_condition_button.clicked.connect(self.add_condition_row)
        self.logic_and_button.clicked.connect(lambda: self.set_logic_operator(LogicOperator.AND))
        self.logic_or_button.clicked.connect(lambda: self.set_logic_operator(LogicOperator.OR))
        self.run_button.clicked.connect(self.start_execution)
        self.viewer_filter_apply_button.clicked.connect(self.apply_viewer_filter)
        self.viewer_filter_clear_button.clicked.connect(self.clear_viewer_filter)
        self.viewer_filter_value_edit.returnPressed.connect(self.apply_viewer_filter)

    def _on_language_changed(self) -> None:
        language = str(self.language_combo.currentData() or "zh_CN")
        self.language_manager.set_language(language)
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        t = self.language_manager.text
        self.setWindowTitle(t("app.title"))
        self.hero_title.setText(t("app.title"))
        self.hero_subtitle.setText(t("app.subtitle"))

        for index, (language_code, translation_key) in enumerate(SUPPORTED_LANGUAGES):
            self.language_combo.setItemText(index, t(translation_key))
            if self.language_combo.itemData(index) == self.language_manager.language:
                self.language_combo.setCurrentIndex(index)

        self.step1_card.set_title_subtitle(t("step1.title"), t("step1.subtitle"))
        self.excel_label.setText(t("step1.excel"))
        self.sheet_label.setText(t("step1.sheet"))
        self.summary_label.setText(t("step1.summary"))
        self.choose_excel_button.setText(t("step1.choose_file"))
        self.load_sheet_button.setText(t("step1.load_sheet"))

        self.step2_card.set_title_subtitle(t("step2.title"), t("step2.subtitle"))
        self.logic_label.setText(t("step2.logic"))
        self.logic_and_button.setText(t("step2.logic_and"))
        self.logic_or_button.setText(t("step2.logic_or"))
        self.auto_match_hint.setText(t("step2.auto_match_hint"))
        self.add_condition_button.setText(t("step2.add"))

        self.step3_card.set_title_subtitle(t("step3.title"), t("step3.subtitle"))
        self.input_label.setText(t("step3.input"))
        self.output_label.setText(t("step3.output"))
        self.choose_input_button.setText(t("step3.choose_input"))
        self.choose_output_button.setText(t("step3.choose_output"))
        self.recursive_checkbox.setText(t("step3.recursive"))
        self.run_button.setText(t("run.button"))
        self.status_label.setText(t(self._status_key))

        self.viewer_card.set_title_subtitle(t("viewer.title"), t("viewer.subtitle"))
        self.viewer_filter_label.setText(t("viewer.filter.label"))
        self.viewer_filter_value_edit.setPlaceholderText(t("viewer.filter.value"))
        self.viewer_filter_apply_button.setText(t("viewer.filter.apply"))
        self.viewer_filter_clear_button.setText(t("viewer.filter.clear"))
        self.viewer_placeholder.setText(t("viewer.placeholder"))

        self.results_section.set_title_subtitle(t("results.title"), t("results.subtitle"))
        self.metric_cards["scanned"].set_caption(t("results.scanned"))
        self.metric_cards["matched_files"].set_caption(t("results.matched_files"))
        self.metric_cards["unmatched"].set_caption(t("results.unmatched"))
        self.metric_cards["conflicts"].set_caption(t("results.conflicts"))
        self.metric_cards["filtered"].set_caption(t("results.filtered"))
        self.metric_cards["matched_records"].set_caption(t("results.matched_records"))
        self.auto_columns_label.setText(t("results.auto_columns"))
        self.results_table.setHorizontalHeaderLabels(
            [
                t("results.table.row"),
                t("results.table.key_field"),
                t("results.table.key_value"),
                t("results.table.files"),
                t("results.table.status"),
            ]
        )

        self.details_section.set_title_subtitle(t("details.title"), t("details.subtitle"))
        self.details_body.setText(t("details.body"))

        for row in self.condition_rows:
            row.retranslate()

        self._refresh_logic_buttons()
        self._refresh_condition_row_state()
        self._update_action_widths()
        self._update_summary_text()
        self._refresh_viewer_filter_fields()
        if self.sheet_loaded:
            self.apply_viewer_filter()
        else:
            self._show_viewer_placeholder()

    def _update_action_widths(self) -> None:
        fixed_buttons = [
            self.choose_excel_button,
            self.load_sheet_button,
            self.choose_input_button,
            self.choose_output_button,
            self.add_condition_button,
            self.viewer_filter_apply_button,
            self.viewer_filter_clear_button,
        ]
        for button in fixed_buttons:
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            button.setMinimumWidth(button.sizeHint().width() + 10)

        self.logic_and_button.setMinimumWidth(max(96, self.logic_and_button.sizeHint().width() + 12))
        self.logic_or_button.setMinimumWidth(max(96, self.logic_or_button.sizeHint().width() + 12))
        self.run_button.setMinimumWidth(max(190, self.run_button.sizeHint().width() + 16))
        self.status_label.setMinimumWidth(max(108, self.status_label.sizeHint().width() + 16))
        self.language_combo.setMinimumWidth(max(152, self.language_combo.sizeHint().width() + 18))
        self.viewer_filter_column_combo.setMinimumWidth(
            max(176, self.viewer_filter_column_combo.sizeHint().width() + 18)
        )

    def _refresh_logic_buttons(self) -> None:
        and_checked = self.logic_operator == LogicOperator.AND
        self.logic_and_button.setChecked(and_checked)
        self.logic_or_button.setChecked(not and_checked)
        for button, checked in (
            (self.logic_and_button, and_checked),
            (self.logic_or_button, not and_checked),
        ):
            button.setProperty("checked", checked)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def _update_summary_text(self) -> None:
        t = self.language_manager.text
        if not self.sheet_loaded:
            self.summary_value.setText(t("step1.summary_empty"))
            return

        columns = [str(column) for column in self.current_dataframe.columns.tolist()]
        preview_fields = ", ".join(columns[:6])
        if len(columns) > 6:
            preview_fields = f"{preview_fields} ..."
        self.summary_value.setText(
            t(
                "step1.summary_loaded",
                rows=len(self.current_dataframe.index),
                columns=len(columns),
                fields=preview_fields or "-",
            )
        )

    def set_logic_operator(self, operator: LogicOperator) -> None:
        self.logic_operator = operator
        self._refresh_logic_buttons()

    def add_condition_row(self) -> None:
        row = ConditionRow(self.language_manager, self.current_dataframe.columns.tolist())
        row.remove_requested.connect(self.remove_condition_row)
        self.condition_rows.append(row)
        self.conditions_layout.addWidget(row)
        self._refresh_condition_row_state()

    def remove_condition_row(self, row: ConditionRow) -> None:
        if len(self.condition_rows) <= 1:
            return
        self.condition_rows.remove(row)
        row.setParent(None)
        row.deleteLater()
        self._refresh_condition_row_state()

    def _refresh_condition_row_state(self) -> None:
        for row in self.condition_rows:
            row.set_fields(self.current_dataframe.columns.tolist())
            row.set_remove_enabled(len(self.condition_rows) > 1)

    def _refresh_viewer_filter_fields(self) -> None:
        current_field = str(self.viewer_filter_column_combo.currentData() or "")
        self.viewer_filter_column_combo.blockSignals(True)
        self.viewer_filter_column_combo.clear()
        self.viewer_filter_column_combo.addItem(
            self.language_manager.text("viewer.filter.all_columns"),
            "",
        )
        for field in self.current_dataframe.columns.tolist():
            self.viewer_filter_column_combo.addItem(str(field), str(field))
        if current_field and current_field in self.current_dataframe.columns:
            self.viewer_filter_column_combo.setCurrentIndex(self.viewer_filter_column_combo.findData(current_field))
        self.viewer_filter_column_combo.blockSignals(False)

    def _show_viewer_placeholder(self) -> None:
        self.viewer_stack.setCurrentIndex(0)
        self.viewer_rows_label.setText(self.language_manager.text("viewer.rows_empty"))

    def choose_excel_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.language_manager.text("step1.choose_file"),
            str(self.project_root),
            "Excel Files (*.xlsx *.xlsm *.xls)",
        )
        if not file_path:
            return
        self.excel_path_edit.setText(file_path)
        self.load_excel_metadata(Path(file_path))

    def choose_directory(self, target_edit: QLineEdit) -> None:
        current_path = target_edit.text().strip()
        start_path = current_path if current_path else str(self.project_root)
        directory = QFileDialog.getExistingDirectory(self, self.windowTitle(), start_path)
        if directory:
            target_edit.setText(directory)

    def load_excel_metadata(self, excel_path: Path | None = None) -> None:
        excel_path = excel_path or Path(self.excel_path_edit.text())
        try:
            self.current_sheet_names = ExcelService.list_sheets(excel_path)
        except Exception as exc:
            self.sheet_loaded = False
            self.current_dataframe = pd.DataFrame()
            self._refresh_condition_row_state()
            self._refresh_viewer_filter_fields()
            self._update_summary_text()
            self._show_viewer_placeholder()
            QMessageBox.critical(
                self,
                self.language_manager.text("dialog.error.title"),
                self.language_manager.text("dialog.load_excel_error", message=str(exc)),
            )
            return

        self.sheet_combo.blockSignals(True)
        self.sheet_combo.clear()
        for sheet_name in self.current_sheet_names:
            self.sheet_combo.addItem(sheet_name, sheet_name)
        self.sheet_combo.blockSignals(False)
        if self.current_sheet_names:
            self.sheet_combo.setCurrentIndex(0)
            self.load_selected_sheet()

    def load_selected_sheet(self) -> None:
        excel_text = self.excel_path_edit.text().strip()
        sheet_name = str(self.sheet_combo.currentData() or "")
        if not excel_text or not sheet_name:
            return

        try:
            self.current_dataframe = ExcelService.read_sheet(Path(excel_text), sheet_name)
        except Exception as exc:
            self.sheet_loaded = False
            self.current_dataframe = pd.DataFrame()
            self._refresh_condition_row_state()
            self._refresh_viewer_filter_fields()
            self._update_summary_text()
            self._show_viewer_placeholder()
            QMessageBox.critical(
                self,
                self.language_manager.text("dialog.error.title"),
                self.language_manager.text("dialog.load_excel_error", message=str(exc)),
            )
            return

        self.sheet_loaded = True
        self.viewer_filter_value_edit.clear()
        self._refresh_condition_row_state()
        self._refresh_viewer_filter_fields()
        self._update_summary_text()
        self.apply_viewer_filter()

    def _display_viewer_dataframe(self, dataframe: pd.DataFrame) -> None:
        display_frame = dataframe.fillna("").astype(str)
        self.viewer_stack.setCurrentIndex(1)
        self.preview_table.setSortingEnabled(False)
        self.preview_table.clear()
        self.preview_table.setRowCount(len(display_frame.index))
        self.preview_table.setColumnCount(len(display_frame.columns))
        self.preview_table.setHorizontalHeaderLabels([str(column) for column in display_frame.columns])

        for row_index, (_, row) in enumerate(display_frame.iterrows()):
            for column_index, value in enumerate(row.tolist()):
                self.preview_table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

        for column_index in range(len(display_frame.columns)):
            self.preview_table.resizeColumnToContents(column_index)
            if self.preview_table.columnWidth(column_index) > 260:
                self.preview_table.setColumnWidth(column_index, 260)

        self.preview_table.setSortingEnabled(True)
        self.preview_table._apply_masks()
        self.viewer_rows_label.setText(
            self.language_manager.text(
                "viewer.rows_info",
                shown=len(display_frame.index),
                total=len(self.current_dataframe.index),
            )
        )

    def apply_viewer_filter(self) -> None:
        if not self.sheet_loaded:
            self._show_viewer_placeholder()
            return

        keyword = self.viewer_filter_value_edit.text().strip().casefold()
        selected_field = str(self.viewer_filter_column_combo.currentData() or "")

        if not keyword:
            filtered = self.current_dataframe.copy()
        elif selected_field:
            series = self.current_dataframe[selected_field].fillna("").astype(str).str.casefold()
            filtered = self.current_dataframe.loc[series.str.contains(keyword, regex=False)]
        else:
            searchable = self.current_dataframe.fillna("").astype(str).apply(lambda column: column.str.casefold())
            mask = searchable.apply(lambda row: row.str.contains(keyword, regex=False).any(), axis=1)
            filtered = self.current_dataframe.loc[mask]

        self._display_viewer_dataframe(filtered)

    def clear_viewer_filter(self) -> None:
        self.viewer_filter_value_edit.clear()
        self.viewer_filter_column_combo.setCurrentIndex(0)
        self.apply_viewer_filter()

    def _collect_conditions(self) -> list:
        return [row.condition() for row in self.condition_rows]

    def _set_busy(self, busy: bool) -> None:
        self.run_button.setEnabled(not busy)
        self.progress_bar.setVisible(busy)
        self._status_key = "run.running" if busy else "run.idle"
        self.status_label.setText(self.language_manager.text(self._status_key))

    def start_execution(self) -> None:
        if self._worker_thread and self._worker_thread.isRunning():
            return

        excel_path = self.excel_path_edit.text().strip()
        sheet_name = str(self.sheet_combo.currentData() or "")
        input_dir = self.input_path_edit.text().strip()
        output_dir = self.output_path_edit.text().strip()
        conditions = self._collect_conditions()

        if (
            not excel_path
            or not sheet_name
            or not input_dir
            or not output_dir
            or not any(condition.is_active for condition in conditions)
        ):
            QMessageBox.warning(
                self,
                self.language_manager.text("dialog.error.title"),
                self.language_manager.text("dialog.error.invalid"),
            )
            return

        options = ExecutionOptions(
            excel_path=Path(excel_path),
            sheet_name=sheet_name,
            input_dir=Path(input_dir),
            output_dir=Path(output_dir),
            recursive=self.recursive_checkbox.isChecked(),
        )

        self._worker_thread = QThread(self)
        self._worker = ExecutionWorker(options, conditions, self.logic_operator)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._on_execution_finished)
        self._worker.failed.connect(self._worker_thread.quit)
        self._worker.failed.connect(self._on_execution_failed)
        self._worker_thread.finished.connect(self._cleanup_worker)

        self._set_busy(True)
        self._worker_thread.start()

    def _cleanup_worker(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None
        if self._worker_thread is not None:
            self._worker_thread.deleteLater()
            self._worker_thread = None

    def _on_execution_finished(self, report: ExecutionReport) -> None:
        self._set_busy(False)
        self._populate_results(report)
        if QMessageBox.question(
            self,
            self.language_manager.text("dialog.open_output.title"),
            self.language_manager.text("dialog.open_output.body"),
        ) == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_path_edit.text().strip()))

    def _on_execution_failed(self, message: str) -> None:
        self._set_busy(False)
        QMessageBox.critical(
            self,
            self.language_manager.text("dialog.error.title"),
            self.language_manager.text("dialog.run_error", message=message),
        )

    def _populate_results(self, report: ExecutionReport) -> None:
        self.metric_cards["scanned"].set_value(str(report.scanned_files))
        self.metric_cards["matched_files"].set_value(str(report.matched_files))
        self.metric_cards["unmatched"].set_value(str(report.unmatched_records))
        self.metric_cards["conflicts"].set_value(str(report.conflict_records))
        self.metric_cards["filtered"].set_value(str(report.filtered_records))
        self.metric_cards["matched_records"].set_value(str(report.matched_records))

        auto_columns = ", ".join(profile.name for profile in report.selected_columns) or self.language_manager.text(
            "results.empty"
        )
        self.auto_columns_value.setText(auto_columns)

        self.results_table.setRowCount(len(report.record_matches))
        for row_index, record_match in enumerate(report.record_matches):
            if record_match.conflict:
                status = self.language_manager.text("status.conflict")
            elif record_match.matched:
                status = self.language_manager.text("status.matched")
            else:
                status = self.language_manager.text("status.missing")

            files_text = "\n".join(path.name for path in record_match.source_paths)
            items = [
                QTableWidgetItem(str(record_match.record_number)),
                QTableWidgetItem(record_match.key_field or "-"),
                QTableWidgetItem(record_match.key_value or "-"),
                QTableWidgetItem(files_text or "-"),
                QTableWidgetItem(status),
            ]
            for column_index, item in enumerate(items):
                self.results_table.setItem(row_index, column_index, item)
        self.results_table._apply_masks()


def create_application() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
