from pathlib import Path

from qgis.PyQt import uic
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
    Path(__file__).resolve().parent / "WgtDoubleCmbBoxSelector.ui"
)


class DoubleCmbBoxSelectionPanel(BASE, WIDGET):
    def __init__(
        self,
        parent,
        dialog_type: str,
        default_selected_metric: str = "",
        input_raster_layer_param_name: str = "",
    ):
        super().__init__()
        self.setupUi(self)
        self.dialog = parent
        self.dialog_type: str = dialog_type
        self.default_selected_metric: str = default_selected_metric
        self.input_raster_layer_param_name: str = input_raster_layer_param_name
        self.fast_mode: bool = False

        self.metrics: dict[str, list[str]] = {}

        self.set_metrics()
        self.populate_metric_filter_combobox()
        self.populate_metric_combobox()

        # set actions
        self.combobox_filter.currentIndexChanged.connect(self.populate_metric_combobox)

        if self.dialog_type == DIALOG_STANDARD:
            self.lineEdit_selected_metric.setVisible(False)
        else:
            self.lineEdit_selected_metric.setVisible(True)
            self.combobox_metric.currentIndexChanged.connect(
                self.set_selected_metric_line_edit_value
            )

    def set_fast_mode(self, fast_mode: bool):
        """Set the fast mode"""
        self.fast_mode = fast_mode
        self.set_metrics()
        self.populate_metric_filter_combobox()

    def set_selected_metric_line_edit_value(self):
        """Set the value of the lineEdit_selected_metric based on the selected value in the combobox_metric"""
        selected_metric: str = self.combobox_metric.currentText()
        if selected_metric:
            self.lineEdit_selected_metric.setText(selected_metric)
        else:
            self.lineEdit_selected_metric.setText("")

    def populate_metric_filter_combobox(self):
        """Populate the combobox_filter based on the keys in the metrics dict"""
        self.combobox_filter.clear()
        self.combobox_filter.addItems(self.metrics.keys())
        self.combobox_filter.setCurrentText(self.default_selected_metric)

    def populate_metric_combobox(self):
        """Populate the combobox_metric based on the selected value in the combobox_filter"""
        metric_group_filter: str = self.combobox_filter.currentText()

        self.combobox_metric.clear()

        if self.metrics and metric_group_filter in self.metrics.keys():
            self.combobox_metric.addItems(self.metrics[metric_group_filter])

    def set_metrics(self):
        """Set the metrics dictionnary based on the input raster layer"""

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
            raster_values=[int(value) for value in raster_int_values if value != 0],
            fast_mode=self.fast_mode,
        )

    def getValue(self):
        if self.dialog_type == DIALOG_STANDARD:
            return self.combobox_metric.currentText()
        else:
            return self.lineEdit_selected_metric.text()

    def text(self):
        if self.dialog_type == DIALOG_STANDARD:
            return self.combobox_metric.currentText()
        else:
            return self.lineEdit_selected_metric.text()

    def setValue(self, value: str):
        # TODO : also set the value of the combobox_metric + combobox_filter based on the value
        self.lineEdit_selected_metric.setText(value)
        # self.populate_metric_combobox()
