from pathlib import Path
from typing import Union

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QSpinBox,
    QDoubleSpinBox,
)


WIDGET, BASE = uic.loadUiType(
    Path(__file__).resolve().parent / "WgtNumberListSelector.ui"
)


class NumberListSelectionPanel(BASE, WIDGET):
    def __init__(self, as_float: bool = False):
        super().__init__()
        self.setupUi(self)

        self.spinbox = QSpinBox() if not as_float else QDoubleSpinBox()

        self.verticalLayout_spinbox.addWidget(self.spinbox)

        self.pushButton_add.clicked.connect(self.add_item_to_destination_list)
        self.pushButton_remove.clicked.connect(self.remove_item_from_destination_list)
        self.pushButton_clear.clicked.connect(self.clear_destination_list)
        self.listWidget_destination.doubleClicked.connect(
            self.remove_item_from_destination_list
        )

    def init_gui(self):
        """Init the gui"""
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def set_spinbox_value(self, value: Union[int, float]):
        """Set the spinbox value"""
        self.spinbox.setValue(value)

    def set_spinbox_minimum_value(self, value: Union[int, float]):
        """Set the spinbox minimum value"""
        self.spinbox.setMinimum(value)

    def set_spinbox_maximum_value(self, value: Union[int, float]):
        """Set the spinbox minimum value"""
        self.spinbox.setMaximum(value)

    def set_spinbox_steps(self, step_value: int):
        """Set the spinbox single step value"""
        self.spinbox.setSingleStep(step_value)

    def add_item_to_destination_list(self) -> None:
        """Add spinbox value to destination list if it's not already in the list"""
        if str(self.spinbox.value()) not in [
            self.listWidget_destination.item(i).text()
            for i in range(self.listWidget_destination.count())
        ]:
            self.listWidget_destination.addItem(str(self.spinbox.value()))
        self.set_properties_value()

    def remove_item_from_destination_list(self) -> None:
        """Remove selected items from destination list"""
        for item in self.listWidget_destination.selectedItems():
            self.listWidget_destination.takeItem(self.listWidget_destination.row(item))
        self.set_properties_value()

    def clear_destination_list(self) -> None:
        """Clear destination list"""
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
        """Set the value of the properties based on the items in the destination list widget."""
        self.lineEdit_propertie_value.setText(value)
