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
from qgis.PyQt import uic
from qgis.core import QgsRasterLayer, QgsProject
from ....helpers.helpers import get_metrics, get_non_empty_value

WIDGET, BASE = uic.loadUiType(
    Path(__file__).resolve().parent / "WgtDoubleCmbBoxSelector.ui"
)


class DoubleCmbBoxSelectionPanel(BASE, WIDGET):
    def __init__(
        self,
        dialog,
        alg,
        metrics={},
        initialValue=None,
        rasterLayerParamName=None,
        standardGui=True,
    ):
        super(DoubleCmbBoxSelectionPanel, self).__init__(None)
        self.setupUi(self)
        self.dialog = dialog
        self.alg = alg
        self.metrics = metrics
        self.initialValue = initialValue
        self.standardGui = standardGui
        self.rasterLayerParamName = rasterLayerParamName
        self.cbFilter.currentIndexChanged.connect(self.update_metrics)

        self.cbFilter.addItems(self.metrics.keys())
        self.update_metrics()
        self.cbFilter.setCurrentText(self.initialValue)

        if self.standardGui:
            self.lineEdit.setVisible(False)
        else:
            self.lineEdit.setVisible(True)
            self.cbValue.currentIndexChanged.connect(self.update_metric_lineEdit)

    def update_metric_lineEdit(self):
        metric = self.cbValue.currentText()
        if metric:
            self.lineEdit.setText(metric)
        else:
            self.lineEdit.setText("")

    def update_metrics(self):
        filter_txt = self.cbFilter.currentText()
        w_value = self.cbValue
        w_value.clear()
        if self.metrics:
            if filter_txt in self.metrics.keys():
                w_value.addItems(self.metrics[filter_txt])

    def calculate_metrics(self):
        rasterLayerParam = (
            self.dialog.mainWidget().wrappers[self.rasterLayerParamName].value()
        )
        if re.match(r"^[a-zA-Z0-9_]+$", rasterLayerParam):
            selectedLayer = QgsProject.instance().mapLayer(rasterLayerParam)
            rasterLayerParam = selectedLayer.dataProvider().dataSourceUri()
        if rasterLayerParam is None:
            return
        elif isinstance(rasterLayerParam, QgsRasterLayer):
            rasterLayerParam = rasterLayerParam.dataProvider().dataSourceUri()
        elif not isinstance(rasterLayerParam, str):
            rasterLayerParam = str(rasterLayerParam)
        int_values_and_nodata = get_non_empty_value(raster_file_path=rasterLayerParam)
        self.metrics = get_metrics(raster_values=int_values_and_nodata)

    def getValue(self):
        if self.standardGui:
            return self.cbValue.currentText()
        else:
            return self.lineEdit.text()

    def text(self):
        if self.standardGui:
            return self.cbValue.currentText()
        else:
            return self.lineEdit.text()

    def setValue(self, value):
        self.update_metrics()
