from typing import Union
from pathlib import Path
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QMessageBox
from .dataclasses import CombineFactorElement


class FactorTableModel(QStandardItemModel):
    """
    A custom `QStandardItemModel` class that represents the data model for factor table of the combine algorithm widget.

    Methods:
        set_data(self, data: "list[CombineFactorElement]") -> None:
            Sets the data in the model with a list of CombineFactorElement objects.

        has_column_duplicates(self, column_index: int = 0) -> bool:
            Checks if all values in a given column of the model are unique.

        has_empty_layer_names(self, column: int = 0) -> bool:
            Checks if values of a given column are empty or "" and returns a list of layer names that have an empty value.

        get_combine_factor_elements(self, return_string: bool = False) -> "list[CombineFactorElement]":
            Returns a list of CombineFactorElement objects representing each row in the model.
    """

    def __init__(self):
        super().__init__()
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(
            [self.tr("Factor name"), self.tr("Layer name"), self.tr("Layer path")]
        )

    # "list[CombineFactorElement | list[str]]"
    def set_data(self, data: list[Union[CombineFactorElement, list[str]]]) -> None:
        """
        Sets the data in the model with a list of CombineFactorElement objects.

        Args:
            data (list): The list of CombineFactorElement objects.

        Returns:
            None
        """
        self.setRowCount(0)

        for factor in data:
            if factor:
                # with standard dialog the value used is of type CombineFactorElement
                if isinstance(factor, CombineFactorElement):
                    factor_name_item = QStandardItem(factor.factor_name)
                    layer_name_item = QStandardItem(factor.layer_name)
                    layer_path_item = QStandardItem(factor.layer_path.as_posix())
                    layer_id = QStandardItem(factor.layer_id)
                # in modeler dialog the value used is a list of strings because the values are stored in the model xml file as a list of strings
                elif len(factor) == 4:
                    factor_name_item = QStandardItem(factor[0])
                    layer_name_item = QStandardItem(factor[1])
                    layer_path_item = QStandardItem(factor[2])
                    layer_id = QStandardItem(factor[3])
                else:
                    raise TypeError(
                        f"Expected CombineFactorElement or List[str, str, Path, str], but got {type(factor)}"
                    )

                # add row to model
                self.appendRow(
                    [
                        factor_name_item,
                        layer_name_item,
                        layer_path_item,
                        layer_id,
                    ]
                )

    def has_column_duplicates(self, column_index: int = 0) -> bool:
        """ "
        Checks if all values in a given column of the model are unique.

        Args:
            column_index (int, optional): The index of the column to check. Defaults to 0.

        Returns:
            bool: True if there are duplicates, False otherwise.
        """
        values = []
        duplicates: list[str] = []
        for row in range(self.rowCount()):
            item = self.item(row, column_index)
            if item is not None and item.text() != "":
                value = item.text()
                if value in values:
                    duplicates.append(value)
                else:
                    values.append(value)

        if duplicates:
            QMessageBox.critical(
                None,
                self.tr("Duplicated factor names"),
                self.tr(f"Duplicated factor names ({', '.join(duplicates)})"),
            )
            return True
        return False

    def has_empty_layer_names(self, column: int = 0) -> bool:
        """Checks if the values of a given column are empty or ""
        and returns a list of layer names that have an empty value.

        Args:
            column (int, optional): The index of the column to check. Defaults to 0.

        Returns:
            bool: True if any layer name is empty, False otherwise.
        """

        empty_layer_names: list[str] = []
        for row_index in range(self.rowCount()):
            item = self.item(row_index, column)
            if item is None or item.text().strip() == "":
                layer_name_item = self.item(row_index, 1)
                if layer_name_item is not None:
                    empty_layer_names.append(layer_name_item.text())

        if empty_layer_names:
            QMessageBox.critical(
                None,
                self.tr("Rasters with an empty factor name"),
                self.tr(
                    f"Rasters with an empty factor name ({', '.join(empty_layer_names)})"
                ),
            )
            return True
        return False

    def get_combine_factor_elements(
        self, return_string: bool = False
    ) -> list[Union[CombineFactorElement, list[str]]]:
        """Returns a list of CombineFactorElement objects representing each row in the model.

        Args:
            return_string (bool, optional): If True, the returned list is composed of list of strings (in modeler because the values needs to be stored
            in the .model xml file as list of strings).
                If False, the paths will be returned as list of CombineFactorElement objects. Defaults to False.

        Returns:
            list[CombineFactorElement]: A list of CombineFactorElement objects.
        """
        elements = []
        for row in range(self.rowCount()):
            factor_name = self.item(row, 0).text()
            layer_name = self.item(row, 1).text()
            layer_path = Path(self.item(row, 2).text())
            layer_id = self.item(row, 3).text()
            if return_string:
                elements.append([factor_name, layer_name, str(layer_path), layer_id])
            else:
                elements.append(
                    CombineFactorElement(factor_name, layer_name, layer_path, layer_id)
                )
        return elements

    def flags(self, index):
        if index.column() == 0:
            return super().flags(index) | Qt.ItemIsEditable
        else:
            return super().flags(index) & ~Qt.ItemIsEditable
