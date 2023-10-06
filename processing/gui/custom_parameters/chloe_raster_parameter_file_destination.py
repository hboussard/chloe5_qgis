from typing import Any
from qgis.core import (
    QgsProcessingParameters,
    QgsProcessingParameterRasterDestination,
)
from qgis.PyQt.QtCore import QCoreApplication


class ChloeRasterParameterFileDestination(QgsProcessingParameterRasterDestination):
    def __init__(
        self,
        name: str,
        description: str = "",
        defaultValue: Any = None,
        optional: bool = False,
        createByDefault: bool = True,
    ):
        super().__init__(name, description, defaultValue, optional, createByDefault)

    def clone(self):
        copy = ChloeRasterParameterFileDestination(self.name(), self.description())
        return copy

    def defaultFileExtension(self):
        return "tif"

    def createFileFilter(self):
        return f"{QCoreApplication.translate('ChloeAlgorithm', 'Raster files')} GeoTIFF (*.tif);; ASCII (*.asc)"

    def supportedOutputRasterLayerExtensions(self):
        return ["asc", "tif"]

    def parameterAsOutputLayer(self, definition, value, context):
        return super().parameterAsOutputLayer(definition, value, context)

    def isSupportedOutputValue(self, value, context):
        output_path = QgsProcessingParameters.parameterAsOutputLayer(
            self, value, context
        )

        # if Path(output_path).suffix.lower().endswith((".asc", ".tif")):
        #     return False, QCoreApplication.translate(
        #         "ChloeAlgorithm", "Output filename must use a .asc or .tif extension"
        #     )
        return True, ""
