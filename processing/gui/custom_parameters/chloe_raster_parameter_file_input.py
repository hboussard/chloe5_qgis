from typing import Any
from qgis.core import (
    QgsProcessingParameterRasterLayer,
)
from qgis.PyQt.QtCore import QCoreApplication


class ChloeRasterParameterFileInput(QgsProcessingParameterRasterLayer):
    """A custom raster input parameter with file filters on ASC and GeoTIFF files."""

    def __init__(
        self,
        name: str,
        description: str = "",
        defaultValue: Any = None,
        optional: bool = False,
    ):
        super().__init__(name, description, defaultValue, optional)

    def clone(self):
        copy = ChloeRasterParameterFileInput(self.name(), self.description())
        return copy

    def defaultFileExtension(self):
        return "tif"

    def createFileFilter(self):
        return f"{QCoreApplication.translate('ChloeAlgorithm', 'Raster files')} GeoTIFF (*.tif);; ASCII (*.asc)"

    def supportedOutputRasterLayerExtensions(self):
        return ["asc", "tif"]
