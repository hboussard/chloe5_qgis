from processing.gui.wrappers import (
    RasterWidgetWrapper,
    DIALOG_STANDARD,
)
from qgis.gui import QgsProcessingMapLayerComboBox
from qgis.core import QgsRasterLayer


class ChloeAscRasterWidgetWrapper(RasterWidgetWrapper):
    """A widget wrapper for a raster layer selection widget where there is no default selected layer in the combobox."""

    def createWidget(self, dependantWidgetConfig=None):
        widget = super().createWidget()
        if isinstance(widget, QgsProcessingMapLayerComboBox):
            dummy_layer = QgsRasterLayer()
            widget.setLayer(dummy_layer)
        return widget

    def postInitialize(self, widgetWrapperList):
        # no initial selection
        if self.dialogType == DIALOG_STANDARD:
            self.combo.setLayer(None)
