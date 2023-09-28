from qgis.core import (
    QgsProcessingParameterVectorDestination,
)
from qgis.PyQt.QtCore import QCoreApplication


class ChloeCSVParameterFileDestination(QgsProcessingParameterVectorDestination):
    def __init__(self, name, description):
        super().__init__(name, description)

    def defaultFileExtension(self):
        return "csv"

    def createFileFilter(self):
        return (
            f"{QCoreApplication.translate('ChloeAlgorithm', 'CSV files')} (*.csv *.CSV)"
        )
