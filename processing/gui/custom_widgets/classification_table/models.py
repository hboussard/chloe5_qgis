from typing import Set
from qgis.PyQt.QtGui import (
    QStandardItemModel,
    QStandardItem,
)
from qgis.PyQt.QtCore import Qt, pyqtSignal

from .dataclasses import DomainValue, from_string_to_domain


class ClassificationTableModel(QStandardItemModel):
    """
    A custom `QStandardItemModel` class that represents the data model for mapping table of mapping table custom widget.
    """

    # custom signal when model is updated
    signal_model_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels([self.tr("domain"), self.tr("class")])

        self.rowsInserted.connect(self.model_updated)
        self.dataChanged.connect(self.model_updated)
        self.rowsRemoved.connect(self.model_updated)

    def model_updated(self) -> None:
        """Emit signal when model is updated"""
        self.signal_model_updated.emit()

    def set_data(self, data: list[list[str]]) -> None:
        """
        Set the data for the classification table.

        Parameters:
            data (list[list[str]]): The data to be set in the table. Each inner list contains two strings representing the domain and class values.

        Returns:
            None
        """
        self.setRowCount(0)
        for value in data:
            domain_item = QStandardItem(value[0])
            class_item = QStandardItem(value[1])
            self.appendRow([domain_item, class_item])

    def get_data(self) -> list[list[str]]:
        """
        Retrieve the data from the classification table.

        Returns:
            A list of lists containing the domain and mapped class for each row in the table.
            This return type is set so that the data can be used in the modeler (which only uses lists in the model xml file)
        """
        data: list[list[str]] = []
        for row in range(self.rowCount()):
            domain_item = self.item(row, 0)
            class_item = self.item(row, 1)
            if domain_item is not None and class_item is not None:
                domain: str = domain_item.text()
                mapped_class: str = class_item.text()
                if domain and mapped_class:
                    data.append([domain, mapped_class])
        return data

    def clear_data(self):
        """clear the model data"""
        self.removeRows(0, self.rowCount())

    def flags(self, index):
        if index.column() in (0, 1):
            return super().flags(index) | Qt.ItemIsEditable
        else:
            return super().flags(index) & ~Qt.ItemIsEditable

    def domains_overlaps(
        self, domain_to_check: DomainValue, row_to_skip_index: int = -1
    ) -> list[DomainValue]:
        """
        Check if the given domain overlaps with other domains in the table.

        Args:
            domain_to_check (DomainValue): The domain value to check for overlaps.
            row_to_skip_index (int, optional): The index of the row to skip during the overlap check. Defaults to -1.

        Returns:
            list[DomainValue]: A list of overlapping domain values.
        """
        overlapping_domains: list[DomainValue] = []
        for domain in self.get_domains(row_to_skip_index=row_to_skip_index):
            if domain_to_check.to_pandas_interval().overlaps(
                domain.to_pandas_interval()
            ):
                overlapping_domains.append(domain)

        return overlapping_domains

    def get_domains(self, row_to_skip_index: int = -1) -> list[DomainValue]:
        """
        Returns the list of domains as DomainValue objects.

        Args:
            row_to_skip_index (int): The index of the row to skip.

        Returns:
            list[DomainValue]: The list of domains as DomainValue objects.
        """
        domains = []
        for row in range(self.rowCount()):
            if row == row_to_skip_index:
                continue
            domain_item = self.item(row, 0)
            domain = domain_item and domain_item.text()
            domain_value = domain and from_string_to_domain(domain)
            if domain_value:
                domains.append(domain_value)
        return domains

    def values_not_contained_in_domains(self, values: list[float]) -> list[float]:
        """Check if the given values are not contained within the domains of the model.

        Args:
            values (list[float]): The list of values to check.

        Returns:
            list[float]: The list of values that are not covered by any domain in the model.
        """
        # check if all values are in the domains and if not return the list of values not covered
        list_of_domains: list[DomainValue] = self.get_domains()
        raster_to_remove: Set[float] = set()

        if not list_of_domains:
            return values

        for value in values:
            for dom in list_of_domains:
                if value in dom.to_pandas_interval():
                    raster_to_remove.add(value)

        return [value for value in values if value not in raster_to_remove]

    def get_data_as_propertie_list(self) -> str:
        """
        Get the data of the model as a formatted string to be used as a properties value.

        Returns:
            str: A formatted string of the data in the model.
        """
        data = []
        for row in range(self.rowCount()):
            domain_item = self.item(row, 0)
            class_item = self.item(row, 1)
            if domain_item is not None and class_item is not None:
                domain: str = domain_item.text()
                mapped_class: str = class_item.text()
                if domain and mapped_class:
                    data.append(f"({domain}-{mapped_class})")
        return ";".join(data)
