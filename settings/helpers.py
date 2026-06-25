from os import remove
from pathlib import Path
from qgis.core import QgsSettings
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMessageBox
from .constants import (
    DEFAULT_MEMORY_HEAP_SIZE,
    SETTINGS_JAVA_PATH,
    SETTINGS_MEMORY_HEAP_SIZE,
)


def get_java_path() -> Path:
    """gets java path from settings"""
    s: QgsSettings = QgsSettings()
    return Path(s.value(SETTINGS_JAVA_PATH, ""))
    # return Path("C://Program Files//Java//jre-1.8//bin//java.exe")


def check_java_path(java_path: Path) -> bool:
    """checks if java path is valid"""

    if java_path == Path():
        error_message: str = "Le chemin vers Java n'est pas défini"
        QMessageBox.warning(
            None,
            "Chemin vers java non défini",
            error_message,
        )

        iface.messageBar().pushCritical(
            "Chemin vers java non défini",
            error_message,
        )
        return False

    if not java_path.exists():
        error_message: str = "Le chemin vers Java n'est pas valide"
        QMessageBox.warning(
            None,
            "Chemin vers java invalide",
            error_message,
        )

        iface.messageBar().pushCritical(
            "Chemin vers java invalide",
            error_message,
        )
        return False

    return True


def remove_temporary_file(file_path: Path) -> None:
    """removes a temporary file"""
    try:
        remove(str(file_path))
    except OSError:
        QMessageBox.warning(
            None,
            "Erreur lors de la suppression du fichier temporaire",
            "Erreur lors de la suppression du fichier temporaire",
        )
        return


def get_memory_heap_size() -> int:
    """gets memory heap size from settings"""
    s: QgsSettings = QgsSettings()
    return int(s.value(SETTINGS_MEMORY_HEAP_SIZE, DEFAULT_MEMORY_HEAP_SIZE))
