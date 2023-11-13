from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem, QIntValidator
from qgis.PyQt.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QItemDelegate,
    QLineEdit,
    QMessageBox,
)

from ..helpers import value_exists_in_model_column


class IntValueDelegate(QItemDelegate):
    """
    A delegate for handling integer values in a QTableView.

    This delegate provides a QLineEdit editor with a QIntValidator to ensure that only integer values are entered.
    It also checks if the entered value already exists in the model but not in the same row, and displays an error message if it does.
    If the entered value is not a valid integer, it displays an error message as well.

    Args:
        parent (QObject): The parent object of the delegate.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.validator = QIntValidator(self)
        self.validator.setBottom(
            -2147483647
        )  # set the minimum value to the lowest possible integer value

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(self.validator)
        return editor

    def setModelData(self, editor, model, index):
        value_str = editor.text()
        # check if the value already exists in the model but not in the same row

        if value_exists_in_model_column(
            model=model, value=value_str, column_index=0, skip_row_index=index.row()
        ):
            QMessageBox.critical(
                None,
                self.tr("Duplicated value"),
                self.tr(f"Value {value_str} already exists"),
            )
            return
        # convert to int if possible, otherwise return
        try:
            value_int = int(value_str)
        except ValueError:
            QMessageBox.critical(
                None,
                self.tr("Invalid value"),
                self.tr(f"Value {value_str} is not a valid integer"),
            )
            return

        model.setData(index, value_int, Qt.EditRole)


class MappingTableModel(QStandardItemModel):
    """
    A custom `QStandardItemModel` class that represents the data model for mapping table of mapping table custom widget.
    """

    # custom signal when model is updated
    signal_model_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels([self.tr("value"), self.tr("new value")])

        self.rowsInserted.connect(self.model_updated)
        self.rowsInserted.connect(self.on_row_inserted)
        self.dataChanged.connect(self.model_updated)
        self.dataChanged.connect(self.on_data_changed)
        self.rowsRemoved.connect(self.model_updated)

    def model_updated(self) -> None:
        """Emit signal when model is updated"""
        self.signal_model_updated.emit()

    def set_data(self, data: set[tuple[str, str]]) -> None:
        """
        Sets the data in the model with a list of Tuple containing the value and the mapped value.

        Returns:
            None
        """
        self.setRowCount(0)
        for value in data:
            value_item = QStandardItem(value[0])
            mapped_value_item = QStandardItem(value[1])
            # set the data of the item to the value to be able to sort the model by integer value
            value_item.setData(int(value[0]), Qt.DisplayRole)
            self.appendRow([value_item, mapped_value_item])
        self.sort(0)

    def clear_data(self):
        """clear the model data"""
        self.removeRows(0, self.rowCount())

    def flags(self, index):
        if index.column() in (0, 1):
            return super().flags(index) | Qt.ItemIsEditable
        else:
            return super().flags(index) & ~Qt.ItemIsEditable

    def append_row(self, value: str, mapped_value: str) -> None:
        """append a row to the model"""
        if self.value_exists_in_column(value=value, column_index=0):
            QMessageBox.critical(
                None,
                self.tr("Duplicated value"),
                self.tr(f"Value {value} already exists"),
            )
            return
        value_item = QStandardItem(value)
        # set the data of the item to the value to be able to sort the model by integer value
        value_item.setData(int(value[0]), Qt.DisplayRole)
        mapped_value_item = QStandardItem(mapped_value)
        self.appendRow([value_item, mapped_value_item])

    def update_value_in_column(
        self,
        first_column_value: str,
        update_column_index: int,
        new_cell_value: str,
    ):
        """
        Update the value of a cell in the model based on the value of the first column to identify the row.

        Args:
            first_column_value (str): The value of the first column to identify the row to update.
            update_column_index (int): The index of the column to update.
            new_cell_value (str): The new value to set in the cell.

        Returns:
            None
        """
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item is not None and item.text():
                if first_column_value == item.text():
                    self.item(row, update_column_index).setText(new_cell_value)

    def value_exists_in_column(self, value: str, column_index: int = 0) -> bool:
        """ "
        Checks if a value exists in a given column of the model.

        Args:
            column_index (int, optional): The index of the column to check. Defaults to 0.

        Returns:
            bool: True if the value exists, False otherwise.
        """
        for row in range(self.rowCount()):
            item = self.item(row, column_index)
            if item is not None and item.text():
                if value == item.text():
                    return True
        return False

    def get_data_as_propertie_list(self) -> str:
        """
        Get the data of the model as a formatted string to be used as a properties value.

        Returns:
            str: A formatted string of the data in the model.
        """
        data = []
        for row in range(self.rowCount()):
            value_item = self.item(row, 0)
            mapped_value_item = self.item(row, 1)
            if value_item is not None and mapped_value_item is not None:
                value = value_item.text()
                mapped_value = mapped_value_item.text()
                if value and mapped_value:
                    data.append(f"({value},{mapped_value})")
        return ";".join(data)

    def on_row_inserted(self) -> None:
        """
        Called when a row is inserted in the model.
        """
        self.sort(0)

    def on_data_changed(self) -> None:
        """
        Called when a cell is edited in the model.
        """

        self.sort(0)
