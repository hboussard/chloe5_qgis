from qgis.core import QgsVectorLayer
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)

from qgis.core import (
    QgsMessageLog,
    Qgis,
    QgsCoordinateReferenceSystem,
)
from qgis.utils import iface
from pathlib import Path


def layer_field_index(layer: QgsVectorLayer, field_name: str) -> int:
    """Get the index of a field in a layer"""
    field_index: int = -1
    if not layer.isValid():
        error_message: str = f"La couche {layer.name()} n'est pas valide"
        QgsMessageLog.logMessage(error_message, level=Qgis.Critical)
        iface.messageBar().pushMessage(
            "Erreur",
            error_message,
            level=Qgis.Critical,
        )
        return field_index

    field_index = layer.fields().indexFromName(field_name)
    if field_index == -1:
        error_message: str = (
            f"Le champ {field_name} n'existe pas dans la couche {layer.name()}"
        )
        QgsMessageLog.logMessage(error_message, level=Qgis.Critical)
        iface.messageBar().pushMessage(
            "Erreur",
            error_message,
            level=Qgis.Critical,
        )
    return field_index


def get_distinct_attributes_values_from_layer(
    vector_layer: QgsVectorLayer, field_name: str
) -> list[str]:
    """Get distinct attributes values from layer"""
    distinct_attributes = set()
    field_index = layer_field_index(vector_layer, field_name)

    if field_index == -1:
        return []

    for feature in vector_layer.getFeatures():
        value = str(feature.attribute(field_index))
        distinct_attributes.add(value)

    return sorted(distinct_attributes)


def vector_layer_field_is_numeric(
    vector_layer: QgsVectorLayer, field_name: str
) -> bool:
    """Check if the field is a numeric field"""

    field_index = layer_field_index(vector_layer, field_name)

    if field_index == -1:
        return False
    field = vector_layer.fields().field(field_index)
    if not field.isNumeric():
        QMessageBox.critical(
            None, "Erreur", f"le champ {field_name} n'est pas un champ numérique"
        )
        return False
    return True


def path_validator(title_name: str, name_msg: str, folder_path: Path) -> bool:
    """Output folder path validator"""

    # check if value is none
    if folder_path == Path():
        QMessageBox.warning(None, title_name, f"Choisir {name_msg}")
        return False
    # check if file path contains whitespaces
    if " " in str(folder_path):
        QMessageBox.warning(
            None,
            title_name,
            f"Le chemin vers {name_msg} contient des espaces",
        )
        return False
    # check if folder exists

    if not folder_path.exists():
        QMessageBox.warning(
            None,
            title_name,
            f"{name_msg} est introuvable",
        )
        return False

    return True


def input_vector_validator(layer_name_msg: str, file_path: Path) -> bool:
    """Input vector layer validator"""
    msgbox_title: str = "Couche input vectorielle"

    # check if value exists
    if file_path == Path():
        QMessageBox.warning(
            None,
            msgbox_title,
            f"Choisir le fichier shapefile {layer_name_msg}",
        )
        return False

    # check if file exists
    if not file_path.exists():
        QMessageBox.warning(
            None,
            msgbox_title,
            f"Fichier shapefile {layer_name_msg} est introuvable",
        )
        return False
    # check if file path contains whitespaces
    if " " in str(file_path):
        QMessageBox.warning(
            None,
            msgbox_title,
            f"Le chemin vers le fichier shapefile {layer_name_msg} contient des espaces",
        )
        return False
    # check if layer is valid
    layer: QgsVectorLayer = QgsVectorLayer(str(file_path), "input_vector_layer", "ogr")

    if not layer.isValid():
        QMessageBox.warning(
            None,
            msgbox_title,
            f"Le fichier shapefile {layer_name_msg} est invalide",
        )
        return False

    # check if layer's geometry type is polygon
    if not layer.geometryType() == 2:
        QMessageBox.warning(
            None,
            msgbox_title,
            f"Le fichier shapefile {layer_name_msg} n'est pas de type polygone",
        )
        return False

    # check if layer crs is 2154

    if not layer.sourceCrs() == QgsCoordinateReferenceSystem("EPSG:2154"):
        QMessageBox.warning(
            None,
            msgbox_title,
            f"La projection du fichier shapefile {layer_name_msg} n'est pas Lambert-93 (EPSG:2154)",
        )
        return False

    return True
