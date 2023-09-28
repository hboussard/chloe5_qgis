from pathlib import Path
from qgis.core import QgsSettings
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QMessageBox
from .constants import SETTINGS_JAVA_PATH


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

    if not get_java_path().exists():
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
