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
import warnings
from osgeo import gdal
import numpy as np
from math import floor
from re import match

from qgis.PyQt import uic

from qgis.core import QgsRasterLayer, QgsApplication, QgsProject

from ..custom_dialogs.DialListCheckBox import DialListCheckBox
from ....algorithms.helpers.constants import INPUT_RASTER

pluginPath = str(QgsApplication.pkgDataPath())
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    WIDGET, BASE = uic.loadUiType(
        os.path.join(
            pluginPath, "python", "plugins", "processing", "ui", "widgetBaseSelector.ui"
        )
    )


class ValuesSelectionPanel(BASE, WIDGET):
    """Custom widget for values selection"""

    def __init__(
        self,
        dialog,
        alg,
        default=None,
        raster_input_param_name: str = INPUT_RASTER,
        is_batch_gui: bool = False,
    ):
        super(ValuesSelectionPanel, self).__init__(None)
        self.setupUi(self)
        self.dialog = dialog
        self.alg = alg
        self._is_batch_gui = is_batch_gui
        # getting rasterLayer param from its name
        self.rasterLayerParamName = raster_input_param_name

        if hasattr(self.leText, "setPlaceholderText"):
            self.leText.setPlaceholderText("1;2;5;6")

        self.btnSelect.clicked.connect(self.selectRangeValues)  # Bouton "..."

    def selectRangeValues(self):
        """Ranges Values selector
        return item (duck typing)
        """
        # Get initial value
        previous_text = self.leText.text()
        try:
            int_checked_values = list(map(int, previous_text.split(";")))
        except:
            int_checked_values = []
        values = ""

        try:
            if self._is_batch_gui:
                p = self.dialog.mainWidget().wrappers[0][0].value()
            else:
                p = self.dialog.mainWidget().wrappers[self.rasterLayerParamName].value()

            if p is None:
                return
            elif isinstance(p, QgsRasterLayer):
                f_input = p.dataProvider().dataSourceUri()
            elif isinstance(p, str):
                # if p is not a correct path then it is already loaded in QgsProject instance, get the QgsRasterLayer object and the file's full path
                if match(r"^[a-zA-Z0-9_]+$", p):
                    selectedLayer = QgsProject.instance().mapLayer(p)
                    f_input = selectedLayer.dataProvider().dataSourceUri()
                else:
                    f_input = p
            else:
                f_input = str(p)

            # === Test algorithm
            ds = gdal.Open(f_input)  # DataSet
            band = ds.GetRasterBand(1)  # -> band
            array = np.array(band.ReadAsArray())  # -> matrice values
            values = np.unique(array)
            # Add nodata values in numpy array
            values_and_nodata = np.insert(values, 0, band.GetNoDataValue())
            int_values_and_nodata = np.unique(
                [int(floor(x)) for x in values_and_nodata]
            )

            # Dialog list check box
            dial = DialListCheckBox(int_values_and_nodata, int_checked_values)
            result = dial.run()
        except:
            result = ""
            raise
        # result
        self.leText.setText(result)

    def getValue(self):
        return str(self.leText.text())

    def text(self):
        return self.leText

    def setValue(self, value):
        self.leText.setText(value)
