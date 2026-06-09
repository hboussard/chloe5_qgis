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
import tempfile


from .helpers import remove_temporary_file

from ..helpers.helpers import get_console_command, run_command
from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.PyQt import uic

from qgis.core import QgsSettings
from .constants import (
    AVAILABLE_GEOGRAPHIC_CONTEXTS,
    DEFAULT_GEOGRAPHIC_CONTEXT,
    SETTINGS_GEOGRAPHIC_CONTEXT,
    SETTINGS_JAVA_PATH,
)

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
        self.pushButton_apply_geographic_context.clicked.connect(
            self.on_apply_geographic_context_button_clicked
        )

    def showEvent(self, event) -> None:
        """Refresh widget values each time the dialog is opened."""
        super().showEvent(event)
        self.set_widget_values_from_settings()
        self.enable_apply_geographic_context_button()

    def setup_gui(self) -> None:
        """setup gui widget properties"""
        self.populate_geographic_context_combobox()
        self.comboBox_geographic_context.currentIndexChanged.connect(
            self.enable_apply_geographic_context_button
        )
        self.set_widget_values_from_settings()
        self.enable_apply_geographic_context_button()

    def enable_apply_geographic_context_button(self) -> None:
        """Enable the apply geographic context button if the geographic context is changed"""
        settings_value: str = self.s.value(SETTINGS_GEOGRAPHIC_CONTEXT, "") or ""
        selected_index: int = self.comboBox_geographic_context.currentIndex()
        selected_value: str = self.comboBox_geographic_context.currentData() or ""

        if not settings_value:
            enabled = (
                selected_index != -1 and selected_value != DEFAULT_GEOGRAPHIC_CONTEXT
            )
        else:
            enabled = selected_value != settings_value

        self.pushButton_apply_geographic_context.setEnabled(enabled)

    def on_apply_geographic_context_button_clicked(self) -> None:
        """Apply the geographic context"""
        # create a temporary properties file with the value local=<selected_value>
        selected_value: str = self.comboBox_geographic_context.currentData() or ""
        #  check if the selected value is in the available geographic contexts
        if selected_value not in AVAILABLE_GEOGRAPHIC_CONTEXTS.keys():
            QMessageBox.warning(
                self._parent,
                "Localisation",
                "La localisation choisie est invalide",
            )
            return
        # create the temporary properties file
        try:
            temp_properties_file: Path = (
                Path(tempfile.gettempdir()) / "chloe_qgis_geographic_context.properties"
            )
            with open(temp_properties_file, "w", encoding="utf-8") as f:
                f.write(f"local={selected_value}")
        except Exception:
            QMessageBox.warning(
                self._parent,
                "Localisation",
                "Erreur lors de la création du fichier temporaire",
            )
            return

        # run the command to apply the geographic context
        command: str = get_console_command(temp_properties_file)
        # silently run the command but show a message if the command fails
        if not run_command(command):
            QMessageBox.warning(
                self._parent,
                "Localisation",
                "Erreur lors de l'application de la localisation",
            )
            # delete the temporary properties file
            remove_temporary_file(temp_properties_file)
            return

        # apply the geographic context
        self.s.setValue(SETTINGS_GEOGRAPHIC_CONTEXT, selected_value)
        self.enable_apply_geographic_context_button()
        # delete the temporary properties file
        remove_temporary_file(temp_properties_file)
        QMessageBox.information(
            self._parent,
            "Localisation",
            "La localisation a été appliquée avec succès.",
        )

    def populate_geographic_context_combobox(self) -> None:
        """Populate the geographic context combobox with the available geographic contexts"""
        self.comboBox_geographic_context.clear()
        for key, label in AVAILABLE_GEOGRAPHIC_CONTEXTS.items():
            self.comboBox_geographic_context.addItem(label, key)

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

        geographic_context: str = self.s.value(SETTINGS_GEOGRAPHIC_CONTEXT, "")
        index = self.comboBox_geographic_context.findData(geographic_context)
        if index >= 0:
            self.comboBox_geographic_context.setCurrentIndex(index)
        else:
            self.comboBox_geographic_context.setCurrentIndex(0)

    def validate(self) -> None:
        """validate dialog action"""
        if not self.check_mandatory_inputs():
            return

        self.save_settings()

        self.accept()

    def close_dialog(self):
        """close dialog action"""
        self.close()
