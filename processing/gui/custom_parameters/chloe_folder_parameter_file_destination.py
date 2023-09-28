from qgis.core import (
    QgsProcessingParameterFolderDestination,
)


class ChloeParameterFolderDestination(QgsProcessingParameterFolderDestination):
    def __init__(self, name, description):
        super().__init__(name, description)

    def clone(self):
        copy = ChloeParameterFolderDestination(self.name(), self.description())
        return copy
