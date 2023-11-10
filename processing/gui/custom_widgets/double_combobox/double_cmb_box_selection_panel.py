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

from qgis.PyQt import uic
from processing.gui.wrappers import (
    DIALOG_STANDARD,
)
from .....helpers.helpers import (
    get_unique_raster_values_as_int,
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
        super().__init__(None)
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
        raster_int_values: list[int] = get_unique_raster_values_as_int(
            raster_file_path=get_input_raster_param_path(
                dialog_type=self.dialog_type,
                input_raster_layer_param_name=self.input_raster_layer_param_name,
                algorithm_dialog=self.dialog,
            )
        )

        self.metrics = get_metrics(
            raster_values=[value for value in raster_int_values if value != 0],
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
