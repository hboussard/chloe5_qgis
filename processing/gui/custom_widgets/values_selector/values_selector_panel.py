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
from .selector_data_strategy import ValueSelectorStrategy
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


class ValuesSelectorPanel(BASE, WIDGET):
    """Custom widget for values selection"""

    def __init__(
        self,
        selector_strategy: ValueSelectorStrategy,
        placeholder_text: str = "",
    ):
        super().__init__(None)
        self.setupUi(self)
        self.selector_strategy: ValueSelectorStrategy = selector_strategy

        if hasattr(self.leText, "setPlaceholderText"):
            self.leText.setPlaceholderText(placeholder_text)

        self.btnSelect.clicked.connect(
            self.display_value_selection_dialog
        )  # Bouton "..."

    def display_value_selection_dialog(self):
        """Display the value selection dialog"""
        current_selected_values: list[
            str
        ] = self.selector_strategy.get_current_selected_values_from_line_edit(
            self.leText.text()
        )

        data: list[str] = self.selector_strategy.get_data()

        if not data:
            return

        dial = DialListCheckBox(
            data,
            current_selected_values,
        )
        result: list[str] = dial.run()

        self.leText.setText(
            self.selector_strategy.convert_selected_values_to_properties_file_element(
                result
            )
        )

    def getValue(self):
        return str(self.leText.text())

    def text(self):
        return self.leText

    def setValue(self, value):
        self.leText.setText(value)
