from PyQt5.QtWidgets import (
    QComboBox,
    QCompleter,
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel


class CompleterComboBox(QComboBox):
    """
    Custom Combobox with qcompleter
    """

    def __init__(self, parent=None) -> None:
        super(CompleterComboBox, self).__init__(parent)

        self._parent = parent

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

    def setCompleterFilterKeyColum(self, key_column: int) -> None:
        """set the model column filter for the qcompleter"""
        self.filter_model.setSourceModel(self.model())
        self.completer.setCompletionColumn(key_column)
        self.filter_model.setFilterKeyColumn(key_column)
