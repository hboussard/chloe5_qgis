from pathlib import Path
from processing.gui.wrappers import (
    RasterWidgetWrapper,
    MapLayerWidgetWrapper
    DIALOG_STANDARD,
)
from qgis.core import QgsSettings
from qgis.PyQt.QtWidgets import QFileDialog,QCheckBox
from qgis.PyQt.QtCore import QCoreApplication


class ChloeOutputFileWidgetWrapper(MapLayerWidgetWrapper):
    """A widget wrapper for a raster layer selection widget."""

    def createWidget(self, dependantWidgetConfig=None):
        self.fileFilter = "Geotiff (*.tif);;ASCII (*.asc)"
        # Create the default widget for QgsProcessingParameterRasterDestination
        self._widget = super().createWidget()

        # Create a checkbox
        self._checkbox = QCheckBox("Check if true", self._widget)

        # Add the checkbox to the default widget's layout
        self._widget.layout().addWidget(self._checkbox)

        return self._widget

    # overiding this method to redefine fileFilter
    def getFileName(self, initial_value=""):
        """base class method overide. Shows a file open dialog"""
        settings = QgsSettings()
        if Path(initial_value).is_dir():
            path = initial_value
        elif Path(initial_value).parent.is_dir():
            path = Path(initial_value).parent
        elif settings.contains("/Processing/LastInputPath"):
            path = str(settings.value("/Processing/LastInputPath"))
        else:
            path = ""

        filename, selected_filter = QFileDialog.getOpenFileName(
            self.widget, self.tr("Select File"), path, self.fileFilter
        )
        if filename:
            settings.setValue(
                "/Processing/LastInputPath", Path(filename).resolve().parent
            )

        return filename, selected_filter

    def postInitialize(self, widgetWrapperList):
        # no initial selection
        if self.dialogType == DIALOG_STANDARD:
            self.combo.setLayer(None)
