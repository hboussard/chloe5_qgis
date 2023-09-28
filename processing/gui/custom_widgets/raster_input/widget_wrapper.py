from pathlib import Path
from processing.gui.wrappers import (
    RasterWidgetWrapper,
    DIALOG_STANDARD,
)
from qgis.core import QgsSettings
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import QCoreApplication


class ChloeAscRasterWidgetWrapper(RasterWidgetWrapper):
    """A widget wrapper for a raster layer selection widget."""

    def createWidget(self, dependantWidgetConfig=None):
        self.fileFilter = "Geotiff (*.tif);;ASCII (*.asc)"
        return super().createWidget()

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
