# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Plugin Chloe

        description : Chloe 'Plugin Settings' dialog 
                              -------------------
        begin                : 2023-09-26
        author : Daan Guillerme, Hugues Boussard
        copyright            : (C) 2022 by INRAE, FDC22
        email                : daan.guillerme@fdc22.com
        email                : daan.guillerme@fdc22.com, hugues.boussard@inrae.fr

 ***************************************************************************/

"""

from pathlib import Path

from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.PyQt import uic

from qgis.core import QgsSettings
from .constants import SETTINGS_JAVA_PATH

FORM_CLASS, _ = uic.loadUiType(Path(__file__).parent / "settings_dialog.ui")


class SettingsDialog(QDialog, FORM_CLASS):

    """
    Plugin configuration dialog
    """

    def __init__(self, parent=None):
        """constructor"""
        super(SettingsDialog, self).__init__(parent)

        self._parent = parent

        # settings
        self.s = QgsSettings()

        # Setup Ui
        self.setupUi(self)
        self.setup_gui()

        # events
        self.buttonBox.accepted.connect(self.validate)
        self.buttonBox.rejected.connect(self.close_dialog)

    def setup_gui(self) -> None:
        """setup gui widget properties"""
        self.set_widget_values_from_settings()

    def check_mandatory_inputs(self) -> bool:
        """Inputs validation. Checks if mandatory inputs are valid values"""
        # check if path is chosen
        java_path: str = self.mQgsFileWidget_java_path.filePath()
        if not java_path:
            QMessageBox.warning(
                self._parent, "Chemin vers JAVA", "Choisissez un chemin vers JAVA"
            )
            return False
        # check if chosen file exists
        if not Path(java_path).exists():
            QMessageBox.warning(
                self._parent,
                "Chemin vers JAVA",
                "L'executable JAVA choisi est introuvable",
            )
            return False
        return True

    def save_settings(self) -> None:
        """Saves settings from widget values"""
        java_path: str = self.mQgsFileWidget_java_path.filePath()

        self.s.setValue(
            SETTINGS_JAVA_PATH,
            java_path,
        )

    def set_widget_values_from_settings(self) -> None:
        """Sets widget values from settings"""
        # java path
        java_path: str = self.s.value(SETTINGS_JAVA_PATH, "")

        if java_path:
            self.mQgsFileWidget_java_path.setFilePath(java_path)

    def validate(self) -> None:
        """validate dialog action"""
        if not self.check_mandatory_inputs():
            return

        self.save_settings()

        self.accept()

    def close_dialog(self):
        """close dialog action"""
        self.close()
