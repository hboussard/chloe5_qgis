from typing import Any
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterVectorDestination,
)
from qgis.PyQt.QtCore import QCoreApplication


class ChloeCSVParameterFileDestination(QgsProcessingParameterVectorDestination):
    def __init__(
        self,
        name: str,
        description: str = "",
        type: QgsProcessing.SourceType = QgsProcessing.TypeVectorAnyGeometry,
        defaultValue: Any = None,
        optional: bool = False,
        createByDefault: bool = True,
    ):
        super().__init__(
            name, description, type, defaultValue, optional, createByDefault
        )

    def defaultFileExtension(self):
        return "csv"

    def createFileFilter(self):
        return (
            f"{QCoreApplication.translate('ChloeAlgorithm', 'CSV files')} (*.csv *.CSV)"
        )
