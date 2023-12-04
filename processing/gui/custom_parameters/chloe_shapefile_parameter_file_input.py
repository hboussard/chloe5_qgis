from typing import Any
from qgis.core import (
    QgsProcessingParameterVectorLayer,
)
from qgis.PyQt.QtCore import QCoreApplication


class ChloeShapefileParameterFileInput(QgsProcessingParameterVectorLayer):
    """A custom shapefile input parameter with file filters on shp files."""

    def __init__(
        self,
        name: str,
        description: str = "",
        defaultValue: Any = None,
        optional: bool = False,
    ):
        super().__init__(name, description, [], defaultValue, optional)

    def clone(self):
        copy = ChloeShapefileParameterFileInput(self.name(), self.description())
        return copy

    def defaultFileExtension(self):
        return "shp"

    def createFileFilter(self):
        return f"{QCoreApplication.translate('ChloeAlgorithm', 'Shapefile')}(*.shp)"

    def supportedOutputRasterLayerExtensions(self):
        return ["shp"]
