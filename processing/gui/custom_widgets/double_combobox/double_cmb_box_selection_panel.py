# -*- coding: utf-8 -*-

#####################################################################################################
# Chloe - landscape metrics
#
# Copyright 2018 URCAUE-Nouvelle Aquitaine
# Author(s) J-C. Naud, O. Bedel - Alkante (http://www.alkante.com) ;
#           H. Boussard - INRA UMR BAGAP (https://www6.rennes.inra.fr/sad)
#
# Created on Mon Oct 22 2018
# This file is part of Chloe - landscape metrics.
#
# Chloe - landscape metrics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Chloe - landscape metrics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Chloe - landscape metrics.  If not, see <http://www.gnu.org/licenses/>.
#####################################################################################################


from pathlib import Path
import re
from typing import Union

from qgis.PyQt import uic
from qgis.core import QgsRasterLayer, QgsProject
from processing.gui.BatchPanel import BatchPanel
from processing.gui.wrappers import (
    DIALOG_MODELER,
    DIALOG_BATCH,
    DIALOG_STANDARD,
)
from ....helpers.helpers import get_metrics, extract_non_zero_non_nodata_values
from ....gui.chloe_algorithm_dialog import ChloeParametersPanel

WIDGET, BASE = uic.loadUiType(
    Path(__file__).resolve().parent / "WgtDoubleCmbBoxSelector.ui"
)


class DoubleCmbBoxSelectionPanel(BASE, WIDGET):
    def __init__(
        self,
        dialog,
        dialog_type: str,
        default_selected_metric: str = "",
        input_raster_layer_param_name: str = "",
    ):
        super(DoubleCmbBoxSelectionPanel, self).__init__(None)
        self.setupUi(self)
        self.dialog = dialog
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

        return self.extract_raster_layer_path(input_raster_layer_param_value)

    def get_input_raster_parameter_value(
        self, widget: Union[BatchPanel, ChloeParametersPanel]
    ) -> Union[str, None]:
        """Retrieve the input raster layer parameter"""

        if self.dialog_type == DIALOG_BATCH:
            return self.get_batch_input_raster_parameter_value(widget)
        else:
            return widget.wrappers[self.input_raster_layer_param_name].value()

    def get_batch_input_raster_parameter_value(
        self, widget: BatchPanel
    ) -> Union[str, None]:
        """Retrieve the input raster layer parameter in batch mode"""

        for wrapper in widget.wrappers[0]:
            if (
                wrapper is not None
                and wrapper.parameterDefinition().name()
                == self.input_raster_layer_param_name
            ):
                return wrapper.value()
        return None

    def extract_raster_layer_path(
        self, input_raster_layer_param: Union[str, None]
    ) -> str:
        """Extract the raster layer path based on the parameter"""
        if input_raster_layer_param is None:
            return ""

        # if the given input_raster_layer is a qgs map layer id
        if re.match(r"^[a-zA-Z0-9_]+$", input_raster_layer_param):
            selected_layer: QgsRasterLayer = QgsProject.instance().mapLayer(
                input_raster_layer_param
            )
            return selected_layer.dataProvider().dataSourceUri()
        else:
            return input_raster_layer_param

    def set_metrics(self):
        """Set the metrics dictionnary based on the input raster layer"""

        # get raster values
        int_values_and_nodata: list[int] = extract_non_zero_non_nodata_values(
            raster_file_path=self.get_input_raster_param_path()
        )

        self.metrics = get_metrics(
            raster_values=int_values_and_nodata, fast_mode=self.fast_mode
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

    def setValue(self):
        self.populate_metric_combobox()
