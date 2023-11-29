# -*- coding: utf-8 -*-

from pathlib import Path

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QAbstractItemView, QListWidgetItem
from processing.gui.wrappers import (
    DIALOG_STANDARD,
)
from .....helpers.helpers import (
    get_unique_raster_values,
)
from ....helpers.helpers import get_metrics
from ..helpers import (
    get_input_raster_param_path,
)

WIDGET, BASE = uic.loadUiType(
    Path(__file__).resolve().parent / "WgtDoubleListSelector.ui"
)


class DoubleListSelectionPanel(BASE, WIDGET):
    def __init__(
        self,
        parent,
        dialog_type: str,
        default_selected_metric: str = "",
        input_raster_layer_param_name: str = "",
    ):
        super().__init__(None)

        self.setupUi(self)

        self.dialog = parent
        self.dialog_type: str = dialog_type
        self.input_raster_layer_param_name: str = input_raster_layer_param_name
        self.default_selected_metric: str = default_selected_metric
        self.metrics: dict[str, list[str]] = {}

        self.init_gui()

    def init_gui(self) -> None:
        """Init the gui"""
        # Activer la multi selection
        self.listWidget_source.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Activer la multi selection
        self.listWidget_destination.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )

        self.combobox_filter.currentIndexChanged.connect(self.populate_source_list)
        self.pushButton_add.clicked.connect(self.add_single_item_to_destination_list)
        self.pushButton_remove.clicked.connect(self.remove_item_from_destination_list)
        self.pushButton_add_all.clicked.connect(self.add_all_items_to_destination_list)
        self.pushButton_clear.clicked.connect(self.clear_destination_list)
        self.listWidget_source.doubleClicked.connect(
            self.add_single_item_to_destination_list
        )
        self.listWidget_destination.doubleClicked.connect(
            self.remove_item_from_destination_list
        )

        self.set_metrics()
        self.populate_filter_combobox()

    def populate_filter_combobox(self):
        """Populate the filter combobox.

        This method clears the filter combobox and populates it with the available metrics.
        It also sets the current text of the combobox to the default selected metric.
        Finally, it clears the destination list.
        """
        self.combobox_filter.clear()
        self.combobox_filter.addItems(self.metrics.keys())
        self.combobox_filter.setCurrentText(self.default_selected_metric)
        self.clear_destination_list()

    def set_metrics(self) -> None:
        """Set the metrics dictionary based on the input raster layer.

        This method resets the metrics dictionary and retrieves the unique raster values from the input raster layer.
        It then calculates the metrics based on the non-zero raster values and updates the metrics dictionary.

        Args:
            None

        Returns:
            None
        """
        # reset metrics
        self.metrics = {}
        # get raster values
        raster_int_values: list[float] = get_unique_raster_values(
            raster_file_path=get_input_raster_param_path(
                dialog_type=self.dialog_type,
                input_raster_layer_param_name=self.input_raster_layer_param_name,
                algorithm_dialog=self.dialog,
            ),
            as_int=True,
        )

        self.metrics = get_metrics(
            raster_values=[int(value) for value in raster_int_values if value != 0]
        )

    def populate_source_list(self) -> None:
        """
        Populates the source list widget based on the selected metric group filter.

        Returns:
            None
        """
        metric_group_filter: str = self.combobox_filter.currentText()

        self.listWidget_source.clear()

        if self.metrics and metric_group_filter in self.metrics.keys():
            self.listWidget_source.addItems(self.metrics[metric_group_filter])

    def add_item_to_destination_list(self, item: QListWidgetItem) -> None:
        """
        Adds the given item to the destination list if it is not already present.

        Args:
            item (QListWidgetItem): The item to be added to the destination list.
        """
        if item.text() not in [
            self.listWidget_destination.item(i).text()
            for i in range(self.listWidget_destination.count())
        ]:
            self.listWidget_destination.addItem(item.text())

        self.set_properties_value()

    def add_single_item_to_destination_list(self) -> None:
        """
        Adds a single selected item from the source list to the destination list.
        """
        selected_items = self.listWidget_source.selectedItems()
        for item in selected_items:
            self.add_item_to_destination_list(item)

    def remove_item_from_destination_list(self) -> None:
        """
        Removes the selected items from the destination list.

        This method removes the selected items from the destination list widget
        and updates the properties value accordingly.
        """
        selected_items = self.listWidget_destination.selectedItems()

        for item in selected_items:
            self.listWidget_destination.takeItem(self.listWidget_destination.row(item))
        self.set_properties_value()

    def add_all_items_to_destination_list(self) -> None:
        """
        Adds all items from the source list to the destination list.
        """
        for i in range(self.listWidget_source.count()):
            self.add_item_to_destination_list(self.listWidget_source.item(i))

    def clear_destination_list(self) -> None:
        """
        Clears the destination list widget and sets the properties value.
        """
        self.listWidget_destination.clear()
        self.set_properties_value()

    def set_properties_value(self) -> None:
        """
        Sets the value of the properties based on the items in the destination list widget.

        If the destination list widget is empty, the properties value is set to an empty string.
        Otherwise, the properties value is set to a semicolon-separated string of the text of each metric in the destination list widget.
        """
        self.lineEdit_propertie_value.setText("")

        if self.listWidget_destination.count() == 0:
            return

        self.lineEdit_propertie_value.setText(
            ";".join(
                [
                    self.listWidget_destination.item(i).text()
                    for i in range(self.listWidget_destination.count())
                ]
            )
        )

    def getValue(self):
        return self.lineEdit_propertie_value.text()

    def setValue(self, value: str):
        self.lineEdit_propertie_value.setText(value)
