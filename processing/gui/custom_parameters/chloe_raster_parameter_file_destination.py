from qgis.core import (
    QgsProcessingParameters,
    QgsProcessingParameterRasterDestination,
)
from qgis.PyQt.QtCore import QCoreApplication
from pathlib import Path


class ChloeRasterParameterFileDestination(QgsProcessingParameterRasterDestination):
    def __init__(self, name, description):
        super().__init__(name, description)

    def clone(self):
        copy = ChloeRasterParameterFileDestination(self.name(), self.description())
        return copy

    def defaultFileExtension(self):
        return "tif"

    def createFileFilter(self):
        return f"{QCoreApplication.translate('ChloeAlgorithm', 'Raster files')} GeoTIFF (*.tif *.TIF);; ASCII (*.asc *.ASC)"

    def supportedOutputRasterLayerExtensions(self):
        return ["asc", "tif"]

    def parameterAsOutputLayer(self, definition, value, context):
        return super().parameterAsOutputLayer(definition, value, context)

    def isSupportedOutputValue(self, value, context):
        output_path = QgsProcessingParameters.parameterAsOutputLayer(
            self, value, context
        )
        print(Path(output_path).suffix.lower())
        # if Path(output_path).suffix.lower().endswith((".asc", ".tif")):
        #     return False, QCoreApplication.translate(
        #         "ChloeAlgorithm", "Output filename must use a .asc or .tif extension"
        #     )
        return True, ""
