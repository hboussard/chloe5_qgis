# -*- coding: utf-8 -*-

"""
***************************************************************************
    ValuesSelectionPanel.py
    ---------------------
    Date                 : August 2017

        email                : hugues.boussard at inra.fr
***************************************************************************

"""

__author__ = "Jean-Charles Naud"
__date__ = "August 2017"
__copyright__ = "(C) 2017, Jean-Charles Naud"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

import os
from pathlib import Path
from typing import Union
import warnings
from processing.gui.BatchPanel import BatchPanel
from processing.gui.wrappers import (
    DIALOG_MODELER,
    DIALOG_BATCH,
    DIALOG_STANDARD,
)
from qgis.PyQt import uic

from qgis.core import QgsApplication, QgsMessageLog, Qgis

from ..custom_dialogs.DialListCheckBox import DialListCheckBox
from ....algorithms.helpers.constants import INPUT_RASTER
from ....gui.chloe_algorithm_dialog import ChloeParametersPanel
from .....helpers.helpers import extract_non_zero_non_nodata_values
from ..helpers import extract_raster_layer_path, get_parameter_value_from_batch_panel

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

    def get_input_raster_param_path(self) -> str:
        """Get the input raster layer path"""

        if self.dialog_type == DIALOG_MODELER:
            return ""

        widget: Union[BatchPanel, ChloeParametersPanel] = self.dialog.mainWidget()

        if not widget:
            return ""

        input_raster_layer_param_value = self.get_input_raster_parameter_value(widget)

        if input_raster_layer_param_value is None:
            return ""

        return extract_raster_layer_path(input_raster_layer_param_value)

    def get_input_raster_parameter_value(
        self, widget: Union[BatchPanel, ChloeParametersPanel]
    ) -> Union[str, None]:
        """Retrieve the input raster layer parameter"""

        if self.dialog_type == DIALOG_BATCH:
            return get_parameter_value_from_batch_panel(
                widget=widget, parameter_name=self.raster_input_param_name
            )
        else:
            return widget.wrappers[self.raster_input_param_name].value()

    def display_value_selection_dialog(self):
        """Display the value selection dialog"""
        raster_file_path: str = self.get_input_raster_param_path()

        # don't show dialog if no raster is selected in input parameter
        if not raster_file_path:
            return

        int_values_and_nodata: list[int] = extract_non_zero_non_nodata_values(
            raster_file_path=raster_file_path
        )
        current_values: list[int] = self.get_current_selected_values()

        dial = DialListCheckBox(int_values_and_nodata, current_values)
        result: list[int] = dial.run()

        self.leText.setText(";".join(str(value) for value in result))

    def get_current_selected_values(self) -> list[int]:
        """Get the current selected values"""
        current_values: list[int] = []

        if not self.leText.text():
            return current_values

        for value in self.leText.text().split(";"):
            try:
                current_values.append(int(value))
            except ValueError:
                QgsMessageLog.logMessage(
                    self.tr(f"The value {value} is not an integer"),
                    level=Qgis.Critical,
                )
        return current_values

    def getValue(self):
        return str(self.leText.text())

    def text(self):
        return self.leText

    def setValue(self, value):
        self.leText.setText(value)
