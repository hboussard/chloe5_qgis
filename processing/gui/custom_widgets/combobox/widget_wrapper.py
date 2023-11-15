from pathlib import Path
from typing import Union

from processing.gui.wrappers import WidgetWrapper, DIALOG_MODELER
from qgis.PyQt.QtWidgets import QLineEdit, QComboBox
from ....algorithms.helpers.constants import INPUT_FILE_CSV

from ..helpers import (
    csv_file_path_is_valid,
    get_csv_file_headers_list,
    get_parameter_value_from_batch_standard_algorithm_dialog,
)


class ChloeCsvHeadersComboboxWidgetWrapper(WidgetWrapper):
    """
    A wrapper class for a combobox selector based on a CSV input file.

    This class provides methods to create a widget for selecting CSV headers, populate the widget with the headers of the
    CSV file selected in the input parameter, and get the selected header value.
    """

    def createWidget(self, input_csv=INPUT_FILE_CSV, parent_widget_config=None):
        self.input_csv = input_csv
        self.parent_widget_config = parent_widget_config
        # STANDARD GUI
        if self.dialogType == DIALOG_MODELER:
            widget = QLineEdit()
            return widget

        return QComboBox()

    def get_parent_widget_config(self):
        return self.parent_widget_config

    def populate_csv_header_combobox(self):
        """Populate the widget csv mapping combobox using the csv file selected in param.

        This method clears the current items in the combobox and populates it with the headers of the CSV file
        selected in the widget's input parameter. If the CSV file has no headers, the combobox will remain empty.
        """
        self.widget.clear()

        csv_headers_list: list[str] = self.get_csv_input_file_headers()

        if csv_headers_list:
            self.widget.addItems(csv_headers_list)

    def get_csv_input_file_headers(self) -> list[str]:
        """
        Get the headers of the CSV input file.

        Returns:
            A list of strings representing the headers of the CSV input file.
        """

        # get the csv input file param
        input_csv_file: Union[
            str, None
        ] = get_parameter_value_from_batch_standard_algorithm_dialog(
            dialog_type=self.dialogType,
            param_name=self.input_csv,
            algorithm_dialog=self.dialog,
        )

        if input_csv_file is None or not input_csv_file:
            return []

        input_csv_file_path: Path = Path(input_csv_file)

        if not csv_file_path_is_valid(input_csv_file_path):
            return []

        return get_csv_file_headers_list(
            input_csv_file_path, skip_columns_indexes=[0, 1]
        )

    def setValue(self, value):
        """Set value on the widget/component."""
        if self.dialogType == DIALOG_MODELER:
            self.widget.setText(str(value))
        else:
            self.widget.setCurrentText(str(value))

    def value(self):
        """Get value on the widget/component."""
        if self.dialogType == DIALOG_MODELER:
            return self.widget.text()
        else:
            return self.widget.currentText()
