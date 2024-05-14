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

    def createFileFilter(self):
        """Create a file filter for shapefiles.
        Note that the filtering capabilities seem to be limited to the file selection dialog
        and the parameter's configuration, rather than the selection of rasters that are already loaded in the QGIS canvas (combobox selector)
        """
        return f"{QCoreApplication.translate('ChloeAlgorithm', 'Shapefile')}(*.shp)"
