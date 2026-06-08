from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QCompleter,
    QStyledItemDelegate,
    QToolTip,
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QEvent, QModelIndex
from PyQt5.QtGui import QCursor, QStandardItemModel


class _ItemTooltipDelegate(QStyledItemDelegate):
    """Shows the full DisplayRole label when Qt requests an item tooltip."""

    def helpEvent(self, event, view, option, index):
        if event.type() == QEvent.ToolTip and index.isValid():
            text = index.data(Qt.ToolTipRole) or index.data(Qt.DisplayRole)
            if text:
                QToolTip.showText(event.globalPos(), str(text), view)
                return True
        return super().helpEvent(event, view, option, index)


class CompleterComboBox(QComboBox):
    """
    Custom Combobox with qcompleter
    """

    def __init__(self, parent=None) -> None:
        super(CompleterComboBox, self).__init__(parent)

        self._parent = parent
        self._tooltip_viewports: dict = {}

        self.setFocusPolicy(Qt.StrongFocus)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)

        self.filter_model = QSortFilterProxyModel(self)
        self.filter_model.setDynamicSortFilter(True)
        self.filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.filter_model.setSourceModel(self.model())

        self.completer = QCompleter(self.filter_model, self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)

        self.completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.setCompleter(self.completer)

        self.lineEdit().textEdited.connect(self.filter_model.setFilterFixedString)
        self.completer.highlighted.connect(self._on_completer_highlighted)

        self._tooltip_model = None
        self._setup_list_tooltips(self.view())
        self._setup_list_tooltips(self.completer.popup())

    def setModel(self, model) -> None:
        self._disconnect_model_tooltips()
        super().setModel(model)
        self.filter_model.setSourceModel(model)
        self._connect_model_tooltips(model)
        self._setup_list_tooltips(self.view())
        self._setup_list_tooltips(self.completer.popup())

    def addItems(self, texts) -> None:
        self._connect_model_tooltips(self.model())
        super().addItems(texts)

    def clear(self) -> None:
        self._connect_model_tooltips(self.model())
        super().clear()

    def _disconnect_model_tooltips(self) -> None:
        if self._tooltip_model is None:
            return

        try:
            self._tooltip_model.rowsInserted.disconnect(self._sync_item_tooltips)
            self._tooltip_model.modelReset.disconnect(self._sync_item_tooltips)
        except (TypeError, RuntimeError):
            pass

        self._tooltip_model = None

    def _connect_model_tooltips(self, model) -> None:
        if model is None or self._tooltip_model is model:
            return

        self._disconnect_model_tooltips()
        self._tooltip_model = model
        model.rowsInserted.connect(self._sync_item_tooltips)
        model.modelReset.connect(self._sync_item_tooltips)
        self._sync_item_tooltips()

    def _setup_list_tooltips(self, view: QAbstractItemView) -> None:
        view.setMouseTracking(True)
        view.viewport().setMouseTracking(True)
        view.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        view.setItemDelegate(_ItemTooltipDelegate(view))

        viewport = view.viewport()
        if viewport not in self._tooltip_viewports:
            viewport.installEventFilter(self)
            self._tooltip_viewports[viewport] = view

    def _sync_item_tooltips(self, *_args) -> None:
        model = self.model()
        if model is None:
            return

        if isinstance(model, QStandardItemModel):
            for row in range(model.rowCount()):
                item = model.item(row, 0)
                if item is None:
                    continue
                label = item.text()
                if label:
                    item.setToolTip(label)
            return

        for row in range(model.rowCount()):
            index = model.index(row, 0)
            label = index.data(Qt.DisplayRole)
            if label:
                model.setData(index, str(label), Qt.ToolTipRole)

    def _on_completer_highlighted(self, index_or_text) -> None:
        if not isinstance(index_or_text, QModelIndex):
            return

        index = index_or_text
        if not index.isValid():
            QToolTip.hideText()
            return

        text = index.data(Qt.ToolTipRole) or index.data(Qt.DisplayRole)
        if not text:
            QToolTip.hideText()
            return

        popup = self.completer.popup()
        rect = popup.visualRect(index)
        pos = popup.viewport().mapToGlobal(rect.bottomLeft())
        QToolTip.showText(pos, str(text), popup)

    def eventFilter(self, obj, event) -> bool:
        view = self._tooltip_viewports.get(obj)
        if view is not None:
            if event.type() == QEvent.MouseMove:
                index = view.indexAt(event.pos())
                if index.isValid():
                    text = index.data(Qt.ToolTipRole) or index.data(Qt.DisplayRole)
                    if text:
                        QToolTip.showText(QCursor.pos(), str(text), view)
                else:
                    QToolTip.hideText()
            elif event.type() in (QEvent.Leave, QEvent.Hide):
                QToolTip.hideText()

        return super().eventFilter(obj, event)

    def setCompleterFilterKeyColum(self, key_column: int) -> None:
        """set the model column filter for the qcompleter"""
        self.filter_model.setSourceModel(self.model())
        self.completer.setCompletionColumn(key_column)
        self.filter_model.setFilterKeyColumn(key_column)
        self._setup_list_tooltips(self.completer.popup())
