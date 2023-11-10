# -*- coding: utf-8 -*-

from pathlib import Path
from re import match
from typing import Union
import warnings
from processing.gui.wrappers import (
    DIALOG_STANDARD,
)
from qgis.PyQt import uic

from qgis.core import QgsApplication

from ..custom_dialogs.DialListCheckBox import DialListCheckBox
from ....algorithms.helpers.constants import INPUT_RASTER
from .....helpers.helpers import (
    get_unique_raster_values_as_int,
    get_raster_nodata_value,
)
from ..helpers import (
    get_input_raster_param_path,
)

plugin_path = str(QgsApplication.pkgDataPath())
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    WIDGET, BASE = uic.loadUiType(
        str(
            Path(
                plugin_path,
                "python",
                "plugins",
                "processing",
                "ui",
                "widgetBaseSelector.ui",
            )
        )
    )

RASTER_NO_DATA_VALUE_INDICATOR: str = "(No data)"


class ValuesSelectionPanel(BASE, WIDGET):
    """Custom widget for values selection"""

    def __init__(
        self,
        parent,
        input_raster_param_name: str = INPUT_RASTER,
        dialog_type: str = DIALOG_STANDARD,
    ):
        super().__init__(None)
        self.setupUi(self)
        self.dialog = parent
        self.dialog_type: str = dialog_type
        self.raster_input_param_name: str = input_raster_param_name

        if hasattr(self.leText, "setPlaceholderText"):
            self.leText.setPlaceholderText("1;2;5;6")

        self.btnSelect.clicked.connect(
            self.display_value_selection_dialog
        )  # Bouton "..."

    def display_value_selection_dialog(self):
        """Display the value selection dialog"""
        raster_file_path: str = get_input_raster_param_path(
            dialog_type=self.dialog_type,
            input_raster_layer_param_name=self.raster_input_param_name,
            algorithm_dialog=self.dialog,
        )

        # don't show dialog if no raster is selected in input parameter
        if not raster_file_path:
            return

        current_values: list[str] = self.get_current_selected_values(raster_file_path)

        dial = DialListCheckBox(
            self.get_data_from_raster(raster_file_path), current_values
        )
        result: list[str] = dial.run()

        self.leText.setText(
            self.convert_selected_values_to_properties_file_element(result)
        )

    def convert_selected_values_to_properties_file_element(
        self, selected_values: list[str]
    ) -> str:
        """
        Convert the selected values to a string, replacing any instances of the no data value with the actual no data value.
        Args:
            selected_values (list[str]): The list of selected value in the diallist

        Returns: A string formatted for the properties file.
        """
        digit_values: list[str] = []
        for value in selected_values:
            if RASTER_NO_DATA_VALUE_INDICATOR in value:
                digit_match = match(r"^-?\d+", value)
                if digit_match:
                    digit_values.append(digit_match.group())
            else:
                digit_values.append(value)

        return ";".join(digit_values)

    def get_data_from_raster(self, raster_file_path: str) -> list[str]:
        """
        Get the data from the raster.

        Args:
            raster_file_path (str): The file path of the raster.

        Returns:
            list[str]: A list of strings representing the raster data.
        """
        raster_data_list: list[str] = []

        if not raster_file_path:
            return raster_data_list

        raster_values: list[int] = get_unique_raster_values_as_int(
            raster_file_path=raster_file_path
        )
        nodata_value: Union[int, None] = get_raster_nodata_value(
            raster_file_path=raster_file_path
        )

        if nodata_value is not None:
            raster_data_list.append(
                f"{str(nodata_value)} {RASTER_NO_DATA_VALUE_INDICATOR}"
            )

        raster_data_list.extend([str(value) for value in raster_values])
        return raster_data_list

    def get_current_selected_values(self, raster_file_path: str) -> list[str]:
        """
        Get the current selected values from the qlineedit.

        Args:
            raster_file_path (str): The path to the raster file.

        Returns:
            list[str]: A list of the current selected values.
        """
        current_values: list[str] = []

        if not self.leText.text():
            return current_values

        nodata_value: Union[int, None] = get_raster_nodata_value(
            raster_file_path=raster_file_path
        )

        for value in self.leText.text().split(";"):
            if nodata_value is not None and value == str(nodata_value):
                current_values.append(
                    f"{str(nodata_value)} {RASTER_NO_DATA_VALUE_INDICATOR}"
                )
            else:
                current_values.append(value)

        return current_values

    def getValue(self):
        return str(self.leText.text())

    def text(self):
        return self.leText

    def setValue(self, value):
        self.leText.setText(value)
