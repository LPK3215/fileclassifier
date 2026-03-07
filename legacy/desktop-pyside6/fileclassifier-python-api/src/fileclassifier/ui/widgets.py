from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QPainterPath, QRegion
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QScrollArea,
    QScrollBar,
    QSizePolicy,
    QSplitter,
    QSplitterHandle,
    QTableWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from fileclassifier.icons import load_icon
from fileclassifier.i18n import LanguageManager
from fileclassifier.models import MatchMode, QueryCondition


def build_rounded_path(
    rect: QRectF,
    *,
    top_left: int,
    top_right: int,
    bottom_right: int,
    bottom_left: int,
) -> QPainterPath:
    left = rect.left()
    top = rect.top()
    right = rect.right()
    bottom = rect.bottom()

    path = QPainterPath()
    path.moveTo(left + top_left, top)
    path.lineTo(right - top_right, top)
    if top_right:
        path.quadTo(right, top, right, top + top_right)
    else:
        path.lineTo(right, top)
    path.lineTo(right, bottom - bottom_right)
    if bottom_right:
        path.quadTo(right, bottom, right - bottom_right, bottom)
    else:
        path.lineTo(right, bottom)
    path.lineTo(left + bottom_left, bottom)
    if bottom_left:
        path.quadTo(left, bottom, left, bottom - bottom_left)
    else:
        path.lineTo(left, bottom)
    path.lineTo(left, top + top_left)
    if top_left:
        path.quadTo(left, top, left + top_left, top)
    else:
        path.lineTo(left, top)
    path.closeSubpath()
    return path


def apply_rounded_mask(
    widget: QWidget,
    *,
    top_left: int,
    top_right: int,
    bottom_right: int,
    bottom_left: int,
) -> None:
    rect = widget.rect()
    if rect.width() <= 0 or rect.height() <= 0:
        return
    path = build_rounded_path(
        QRectF(rect.adjusted(0, 0, -1, -1)),
        top_left=top_left,
        top_right=top_right,
        bottom_right=bottom_right,
        bottom_left=bottom_left,
    )
    widget.setMask(QRegion(path.toFillPolygon().toPolygon()))


class CardFrame(QFrame):
    def __init__(self, title: str = "", subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CardFrame")
        self.setProperty("card", True)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(14)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("StepTitle")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("CardSubtitle")
        self.subtitle_label.setWordWrap(True)

        self._layout.addWidget(self.title_label)
        self._layout.addWidget(self.subtitle_label)

        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(16)
        self._layout.addLayout(self.body_layout)

    def set_title_subtitle(self, title: str, subtitle: str) -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)


class MetricCard(QFrame):
    def __init__(self, caption: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CardFrame")
        self.setProperty("card", True)
        self.setProperty("metric", True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        self.value_label = QLabel("0")
        self.value_label.setObjectName("MetricValue")
        self.caption_label = QLabel(caption)
        self.caption_label.setObjectName("MetricCaption")
        self.caption_label.setWordWrap(True)

        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_caption(self, caption: str) -> None:
        self.caption_label.setText(caption)


class RoundedSplitterHandle(QSplitterHandle):
    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        apply_rounded_mask(
            self,
            top_left=999,
            top_right=999,
            bottom_right=999,
            bottom_left=999,
        )


class RoundedSplitter(QSplitter):
    def createHandle(self) -> QSplitterHandle:  # type: ignore[override]
        return RoundedSplitterHandle(self.orientation(), self)


class RoundedScrollArea(QScrollArea):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.verticalScrollBar().rangeChanged.connect(self._apply_scrollbar_masks)
        self.horizontalScrollBar().rangeChanged.connect(self._apply_scrollbar_masks)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._apply_scrollbar_masks()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_scrollbar_masks()

    def _apply_scrollbar_masks(self, *args) -> None:
        self._apply_scrollbar_mask(self.verticalScrollBar())
        self._apply_scrollbar_mask(self.horizontalScrollBar())

    def _apply_scrollbar_mask(self, scrollbar: QScrollBar) -> None:
        if not scrollbar.isVisible():
            scrollbar.clearMask()
            return
        apply_rounded_mask(
            scrollbar,
            top_left=999,
            top_right=999,
            bottom_right=999,
            bottom_left=999,
        )


class RoundedTableWidget(QTableWidget):
    def __init__(self, rows: int = 0, columns: int = 0, parent: QWidget | None = None) -> None:
        super().__init__(rows, columns, parent)
        self._corner_radius = 12
        self.verticalScrollBar().rangeChanged.connect(self._apply_masks)
        self.horizontalScrollBar().rangeChanged.connect(self._apply_masks)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._apply_masks()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_masks()

    def _apply_masks(self, *args) -> None:
        self._apply_widget_mask(
            self,
            top_left=self._corner_radius,
            top_right=self._corner_radius,
            bottom_right=self._corner_radius,
            bottom_left=self._corner_radius,
        )

        viewport_bottom_left = 0 if self.horizontalScrollBar().isVisible() else self._corner_radius
        viewport_bottom_right = 0
        if not self.horizontalScrollBar().isVisible() and not self.verticalScrollBar().isVisible():
            viewport_bottom_right = self._corner_radius
        self._apply_widget_mask(
            self.viewport(),
            top_left=0,
            top_right=0,
            bottom_right=viewport_bottom_right,
            bottom_left=viewport_bottom_left,
        )

        top_right_radius = self._corner_radius
        header = self.horizontalHeader()
        self._apply_widget_mask(
            header,
            top_left=self._corner_radius,
            top_right=top_right_radius,
            bottom_right=top_right_radius,
            bottom_left=self._corner_radius,
        )
        # The header paints sections in its viewport; mask both widgets so edge
        # sections keep rounded corners consistently.
        self._apply_widget_mask(
            header.viewport(),
            top_left=self._corner_radius,
            top_right=top_right_radius,
            bottom_right=top_right_radius,
            bottom_left=self._corner_radius,
        )

        vertical_bar = self.verticalScrollBar()
        if vertical_bar.isVisible():
            bottom_right_radius = 0 if self.horizontalScrollBar().isVisible() else self._corner_radius
            self._apply_widget_mask(
                vertical_bar,
                top_left=self._corner_radius,
                top_right=self._corner_radius,
                bottom_right=bottom_right_radius,
                bottom_left=0,
            )
        else:
            vertical_bar.clearMask()

        horizontal_bar = self.horizontalScrollBar()
        if horizontal_bar.isVisible():
            bottom_left_radius = 0 if self.verticalScrollBar().isVisible() else self._corner_radius
            self._apply_widget_mask(
                horizontal_bar,
                top_left=0,
                top_right=0,
                bottom_right=self._corner_radius,
                bottom_left=bottom_left_radius,
            )
        else:
            horizontal_bar.clearMask()

    def _apply_widget_mask(
        self,
        widget: QWidget,
        *,
        top_left: int,
        top_right: int,
        bottom_right: int,
        bottom_left: int,
    ) -> None:
        apply_rounded_mask(
            widget,
            top_left=top_left,
            top_right=top_right,
            bottom_right=bottom_right,
            bottom_left=bottom_left,
        )


class RoundedComboPopupView(QListView):
    def __init__(self, corner_radius: int = 12, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._corner_radius = corner_radius
        self.setProperty("comboPopupView", True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.verticalScrollBar().rangeChanged.connect(self._apply_masks)
        self.horizontalScrollBar().rangeChanged.connect(self._apply_masks)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._apply_masks()
        QTimer.singleShot(0, self._apply_masks)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_masks()

    def _apply_masks(self, *args) -> None:
        vertical_visible = self.verticalScrollBar().isVisible()
        horizontal_visible = self.horizontalScrollBar().isVisible()
        viewport_bottom_left = 0 if horizontal_visible else self._corner_radius
        viewport_bottom_right = 0 if horizontal_visible else self._corner_radius

        self._apply_widget_mask(
            self,
            top_left=self._corner_radius,
            top_right=self._corner_radius,
            bottom_right=self._corner_radius,
            bottom_left=self._corner_radius,
        )
        self._apply_widget_mask(
            self.viewport(),
            top_left=self._corner_radius,
            top_right=self._corner_radius,
            bottom_right=viewport_bottom_right,
            bottom_left=viewport_bottom_left,
        )

        vertical_bar = self.verticalScrollBar()
        if vertical_bar.isVisible():
            bottom_right_radius = 0 if horizontal_visible else self._corner_radius
            bottom_left_radius = 0 if horizontal_visible else self._corner_radius
            self._apply_widget_mask(
                vertical_bar,
                top_left=self._corner_radius,
                top_right=self._corner_radius,
                bottom_right=bottom_right_radius,
                bottom_left=bottom_left_radius,
            )
        else:
            vertical_bar.clearMask()

        horizontal_bar = self.horizontalScrollBar()
        if horizontal_bar.isVisible():
            bottom_left_radius = 0 if vertical_visible else self._corner_radius
            self._apply_widget_mask(
                horizontal_bar,
                top_left=0,
                top_right=0,
                bottom_right=self._corner_radius,
                bottom_left=bottom_left_radius,
            )
        else:
            horizontal_bar.clearMask()

        popup = self.window()
        if popup is not None and popup.windowType() == Qt.WindowType.Popup:
            self._apply_widget_mask(
                popup,
                top_left=self._corner_radius,
                top_right=self._corner_radius,
                bottom_right=self._corner_radius,
                bottom_left=self._corner_radius,
            )

    def _apply_widget_mask(
        self,
        widget: QWidget,
        *,
        top_left: int,
        top_right: int,
        bottom_right: int,
        bottom_left: int,
    ) -> None:
        apply_rounded_mask(
            widget,
            top_left=top_left,
            top_right=top_right,
            bottom_right=bottom_right,
            bottom_left=bottom_left,
        )


class RoundedComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._popup_view = RoundedComboPopupView(parent=self)
        self.setView(self._popup_view)

    def showPopup(self) -> None:  # type: ignore[override]
        super().showPopup()
        self._popup_view._apply_masks()
        QTimer.singleShot(0, self._popup_view._apply_masks)


class CollapsibleSection(QFrame):
    def __init__(self, title: str = "", subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CardFrame")
        self.setProperty("card", True)
        self.setProperty("collapsible", True)
        self._expanded = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        self.toggle_button = QToolButton()
        self.toggle_button.setAutoRaise(True)
        self.toggle_button.setProperty("collapseToggle", True)
        self.toggle_button.setIconSize(QSize(16, 16))
        self.toggle_button.clicked.connect(self.toggle)
        self._sync_toggle_icon()

        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("StepTitle")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("CardSubtitle")
        self.subtitle_label.setWordWrap(True)
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.subtitle_label)

        header_layout.addWidget(self.toggle_button)
        header_layout.addLayout(title_layout, 1)
        layout.addLayout(header_layout)

        self.content_widget = QWidget()
        self.content_widget.setProperty("flatContainer", True)
        self.content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        layout.addWidget(self.content_widget)

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self.content_widget.setVisible(self._expanded)
        self._sync_toggle_icon()

    def set_title_subtitle(self, title: str, subtitle: str) -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)

    def _sync_toggle_icon(self) -> None:
        icon_name = "collapse_down" if self._expanded else "collapse_right"
        self.toggle_button.setIcon(load_icon(icon_name))


class ConditionRow(QWidget):
    remove_requested = Signal(object)

    def __init__(
        self,
        language_manager: LanguageManager,
        fields: Sequence[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.language_manager = language_manager
        self._fields = list(fields or [])
        self.setProperty("conditionRow", True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.field_combo = RoundedComboBox()
        self.mode_combo = RoundedComboBox()
        self.value_edit = QLineEdit()
        self.range_start_edit = QLineEdit()
        self.range_end_edit = QLineEdit()
        self.remove_button = QPushButton()
        self.remove_button.setProperty("danger", True)
        self.remove_button.setIcon(load_icon("remove_condition"))
        self.remove_button.setIconSize(QSize(18, 18))
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self))

        self.range_container = QWidget()
        self.range_container.setProperty("flatContainer", True)
        self.range_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        range_layout = QHBoxLayout(self.range_container)
        range_layout.setContentsMargins(0, 0, 0, 0)
        range_layout.setSpacing(10)
        range_layout.addWidget(self.range_start_edit)
        range_layout.addWidget(self.range_end_edit)

        layout.addWidget(self.field_combo, 2)
        layout.addWidget(self.mode_combo, 1)
        layout.addWidget(self.value_edit, 2)
        layout.addWidget(self.range_container, 2)
        layout.addWidget(self.remove_button)

        self.field_combo.setMinimumWidth(132)
        self.mode_combo.setMinimumWidth(110)
        self.value_edit.setMinimumWidth(160)
        self.range_start_edit.setMinimumWidth(120)
        self.range_end_edit.setMinimumWidth(120)

        self.mode_combo.currentIndexChanged.connect(self._sync_mode_widgets)
        self.set_fields(self._fields)
        self.retranslate()
        self._sync_mode_widgets()

    def selected_field(self) -> str:
        return str(self.field_combo.currentData() or "")

    def selected_mode(self) -> MatchMode:
        return MatchMode(self.mode_combo.currentData())

    def set_fields(self, fields: Sequence[str]) -> None:
        current_field = self.selected_field()
        self._fields = list(fields)
        self.field_combo.blockSignals(True)
        self.field_combo.clear()
        self.field_combo.addItem(self.language_manager.text("step2.field"), "")
        for field in self._fields:
            self.field_combo.addItem(field, field)
        if current_field in self._fields:
            self.field_combo.setCurrentIndex(self.field_combo.findData(current_field))
        self.field_combo.blockSignals(False)

    def condition(self) -> QueryCondition:
        return QueryCondition(
            field_name=self.selected_field(),
            match_mode=self.selected_mode(),
            value=self.value_edit.text().strip(),
            range_start=self.range_start_edit.text().strip(),
            range_end=self.range_end_edit.text().strip(),
        )

    def set_remove_enabled(self, enabled: bool) -> None:
        self.remove_button.setEnabled(enabled)

    def _sync_mode_widgets(self) -> None:
        is_range = self.selected_mode() == MatchMode.RANGE
        self.value_edit.setVisible(not is_range)
        self.range_container.setVisible(is_range)

    def retranslate(self) -> None:
        current_mode = self.mode_combo.currentData()
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        self.mode_combo.addItem(self.language_manager.text("mode.exact"), MatchMode.EXACT.value)
        self.mode_combo.addItem(self.language_manager.text("mode.contains"), MatchMode.CONTAINS.value)
        self.mode_combo.addItem(self.language_manager.text("mode.fuzzy"), MatchMode.FUZZY.value)
        self.mode_combo.addItem(self.language_manager.text("mode.range"), MatchMode.RANGE.value)
        if current_mode:
            self.mode_combo.setCurrentIndex(self.mode_combo.findData(current_mode))
        self.mode_combo.blockSignals(False)

        self.set_fields(self._fields)
        self.value_edit.setPlaceholderText(self.language_manager.text("step2.value"))
        self.range_start_edit.setPlaceholderText(self.language_manager.text("step2.range_start"))
        self.range_end_edit.setPlaceholderText(self.language_manager.text("step2.range_end"))
        self.remove_button.setText(self.language_manager.text("step2.remove"))
        self.remove_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.remove_button.setMinimumWidth(max(118, self.remove_button.sizeHint().width() + 10))
        self._sync_mode_widgets()
