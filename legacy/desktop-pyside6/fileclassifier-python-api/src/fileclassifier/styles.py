from __future__ import annotations

from pathlib import Path


STYLESHEET_TEMPLATE = """
QWidget {
    background: #f6f8fb;
    color: #1f2a37;
    font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background: #f6f8fb;
}

QFrame[card="true"] {
    background: #ffffff;
    border: 1px solid #dbe4f0;
    border-radius: 16px;
}

QFrame[heroCard="true"] {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #ffffff,
        stop: 0.55 #f8fbff,
        stop: 1 #f1f5fa
    );
    border: 1px solid #d9e3ef;
    border-radius: 16px;
}

QFrame[viewerPanel="true"] {
    background: #ffffff;
    border: 1px solid #dbe4ee;
    border-radius: 16px;
}

QFrame[tableShell="true"] {
    background: #ffffff;
    border: 1px solid #d7e2ee;
    border-radius: 16px;
}

QFrame[metric="true"] {
    background: #fbfdff;
    border: 1px solid #e1e8f1;
    border-radius: 16px;
}

QFrame[supportCard="true"] {
    background: #ffffff;
    border: 1px solid #dce5ef;
    border-radius: 16px;
}

QFrame[softStrip="true"] {
    background: #fcfdff;
    border: 1px solid #e3eaf2;
    border-radius: 12px;
}

QWidget[conditionRow="true"],
QWidget[flatContainer="true"] {
    background: transparent;
    border: none;
}

QSplitter::handle:horizontal {
    width: 8px;
    margin: 10px 2px;
    border: 1px solid #d5dfeb;
    border-radius: 999px;
    background: #eef3f8;
}

QSplitter::handle:horizontal:hover {
    background: #dfe8f2;
    border-color: #c0cedf;
}

QLabel#HeroTitle {
    font-size: 26px;
    font-weight: 700;
    color: #163963;
    background: transparent;
}

QLabel#HeroSubtitle {
    font-size: 14px;
    color: #5a7088;
    background: transparent;
}

QLabel#StepTitle {
    font-size: 18px;
    font-weight: 700;
    color: #173a62;
    background: transparent;
}

QLabel[panelTitle="true"] {
    color: #173a62;
    background: #f7fbff;
    border: 1px solid #dae4ef;
    border-radius: 12px;
    padding: 4px 12px;
}

QLabel#SectionLabel {
    font-size: 11px;
    font-weight: 700;
    color: #64778d;
    background: transparent;
}

QLabel#CardSubtitle,
QLabel#BodyText {
    color: #586b80;
    font-size: 13px;
    background: transparent;
}

QLabel#MutedText {
    color: #728497;
    font-size: 12px;
    background: transparent;
}

QLabel#StatusText {
    color: #355372;
    font-size: 12px;
    font-weight: 600;
    background: #eef4fb;
    border: 1px solid #d6e2ef;
    min-height: 40px;
    max-height: 40px;
    border-radius: 12px;
    padding: 0 16px;
}

QLabel#ViewerPlaceholder {
    color: #617489;
    font-size: 15px;
    padding: 24px 36px;
    background: transparent;
    border: none;
}

QLabel#MetricValue {
    font-size: 26px;
    font-weight: 700;
    color: #16477b;
    background: transparent;
}

QLabel#MetricCaption {
    color: #667a90;
    font-size: 12px;
    background: transparent;
}

QPushButton,
QComboBox,
QLineEdit {
    min-height: 40px;
    max-height: 40px;
    border-radius: 12px;
}

QPushButton {
    background: #ffffff;
    color: #1f3852;
    border: 1px solid #cfdae7;
    padding: 0 16px;
    font-weight: 600;
}

QPushButton:hover {
    background: #f4f8fc;
    border-color: #b7c8da;
}

QPushButton:pressed {
    background: #eaf1f8;
}

QPushButton:disabled {
    background: #edf2f7;
    color: #9aa8b7;
    border-color: #d8e1eb;
}

QPushButton[primary="true"] {
    background: #2d67d6;
    color: #ffffff;
    border: 1px solid #2456b4;
}

QPushButton[primary="true"]:hover {
    background: #255bc1;
    border-color: #214fa7;
}

QPushButton[secondary="true"] {
    background: #ffffff;
    color: #214566;
    border: 1px solid #ccd9e8;
}

QPushButton[secondary="true"]:hover {
    background: #f5f8fd;
    border-color: #b8cadf;
}

QPushButton[ghost="true"] {
    background: transparent;
    color: #54697f;
    border: 1px solid #d9e3ee;
}

QPushButton[ghost="true"]:hover {
    background: #f3f7fb;
    color: #2d465f;
}

QPushButton[danger="true"] {
    background: #fff7f6;
    color: #a8433d;
    border: 1px solid #efc3bf;
}

QPushButton[danger="true"]:hover {
    background: #ffefed;
    border-color: #eaa49e;
}

QPushButton[logic="true"] {
    min-width: 84px;
    background: #f4f7fb;
    color: #4f647a;
    border: 1px solid #d6e1ec;
}

QPushButton[logic="true"]:hover {
    background: #edf3fa;
    border-color: #bfd0e2;
}

QPushButton[logic="true"]:checked,
QPushButton[logic="true"][checked="true"] {
    background: #173d68;
    color: #ffffff;
    border: 1px solid #17385e;
}

QToolButton {
    background: transparent;
    color: #47637f;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 4px;
}

QToolButton[collapseToggle="true"] {
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    background: #f2f6fb;
    border: 1px solid #d6e0eb;
}

QToolButton[collapseToggle="true"]:hover {
    background: #e9f0f8;
    border-color: #bfd0e1;
}

QComboBox,
QLineEdit {
    background: #ffffff;
    border: 1px solid #ccd9e6;
    color: #213244;
    padding: 0 14px;
}

QLineEdit[readOnly="true"] {
    background: #f7f9fc;
    color: #42576b;
}

QComboBox:hover,
QLineEdit:hover {
    border-color: #aebfd3;
}

QComboBox:focus,
QLineEdit:focus {
    border: 1px solid #2d67d6;
    background: #ffffff;
}

QComboBox {
    combobox-popup: 0;
    padding-right: 38px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 32px;
    border: none;
    background: transparent;
}

QComboBox::down-arrow {
    image: url("__DROPDOWN_ARROW__");
    width: 10px;
    height: 10px;
}

QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #cfdbe8;
    border-radius: 12px;
    outline: none;
    padding: 6px;
    selection-background-color: transparent;
    selection-color: #173a62;
}

QAbstractItemView[comboPopupView="true"] {
    background: #ffffff;
    border: 1px solid #cfdbe8;
    border-radius: 12px;
    outline: none;
    padding: 6px;
    selection-background-color: transparent;
    selection-color: #173a62;
}

QComboBox QAbstractItemView::item {
    min-height: 34px;
    margin: 2px 0;
    padding: 0 12px;
    border-radius: 10px;
    background: transparent;
}

QAbstractItemView[comboPopupView="true"]::item {
    min-height: 34px;
    margin: 2px 0;
    padding: 0 12px;
    border-radius: 10px;
    background: transparent;
}

QComboBox QAbstractItemView::item:selected {
    background: #e7f0ff;
    color: #173a62;
}

QAbstractItemView[comboPopupView="true"]::item:selected {
    background: #e7f0ff;
    color: #173a62;
}

QComboBox QAbstractItemView::corner {
    background: transparent;
    border: none;
}

QAbstractItemView[comboPopupView="true"]::corner {
    background: transparent;
    border: none;
}

QComboBox QAbstractItemView QScrollBar:vertical {
    margin: 8px 2px 8px 0;
}

QAbstractItemView[comboPopupView="true"] QScrollBar:vertical {
    margin: 8px 2px 8px 0;
}

QComboBox QAbstractItemView QScrollBar:horizontal {
    margin: 0 8px 2px 8px;
}

QAbstractItemView[comboPopupView="true"] QScrollBar:horizontal {
    margin: 0 8px 2px 8px;
}

QCheckBox {
    spacing: 8px;
    color: #23384c;
    background: transparent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 1px solid #93abca;
    background: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #6f8eb6;
}

QCheckBox::indicator:checked {
    background: #2d67d6;
    border-color: #2d67d6;
}

QProgressBar#InlineProgress {
    min-height: 12px;
    max-height: 12px;
    background: #e9eff6;
    border: 1px solid #d6e1ec;
    border-radius: 999px;
    text-align: center;
    color: transparent;
}

QProgressBar#InlineProgress::chunk {
    background: #2d67d6;
    border-radius: 999px;
}

QTableWidget[dataGrid="true"] {
    background: #ffffff;
    alternate-background-color: #f8fbff;
    border: none;
    gridline-color: #ebf1f7;
    selection-background-color: #dce8fb;
    selection-color: #183654;
    outline: none;
}

QTableWidget[dataGrid="true"]::item {
    padding: 8px;
}

QHeaderView {
    background: #eff4fa;
    border: none;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}

QHeaderView::section {
    background: #eff4fa;
    color: #3c5874;
    border: none;
    border-bottom: 1px solid #d7e2ee;
    padding: 10px 12px;
    font-weight: 700;
    border-top-left-radius: 0px;
    border-top-right-radius: 0px;
}

QHeaderView::section:first {
    border-top-left-radius: 12px;
    border-bottom-left-radius: 12px;
}

QHeaderView::section:last {
    border-top-right-radius: 12px;
    border-bottom-right-radius: 12px;
}

QTableCornerButton::section {
    background: transparent;
    border: none;
}

QAbstractScrollArea::corner {
    background: transparent;
    border: none;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #f6f9fc;
    border: 1px solid #dce5ee;
    border-radius: 999px;
    width: 8px;
    margin: 8px 2px 8px 2px;
}

QScrollBar::handle:vertical {
    background: #c2cfdd;
    min-height: 34px;
    border-radius: 999px;
}

QScrollBar::handle:vertical:hover {
    background: #aabed2;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical,
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: transparent;
    border: none;
}

QScrollBar:horizontal {
    background: #f6f9fc;
    border: 1px solid #dce5ee;
    border-radius: 999px;
    height: 8px;
    margin: 2px 8px 2px 8px;
}

QScrollBar::handle:horizontal {
    background: #c2cfdd;
    min-width: 34px;
    border-radius: 999px;
}

QScrollBar::handle:horizontal:hover {
    background: #aabed2;
}
"""


def build_app_stylesheet(dropdown_arrow_path: str | Path) -> str:
    normalized_path = str(dropdown_arrow_path).replace("\\", "/")
    return STYLESHEET_TEMPLATE.replace("__DROPDOWN_ARROW__", normalized_path)


APP_STYLESHEET = build_app_stylesheet("")
