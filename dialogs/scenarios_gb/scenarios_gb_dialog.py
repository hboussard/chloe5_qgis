from pathlib import Path
from qgis.PyQt.QtWidgets import (
    QDialog,
    QPushButton,
    QDialogButtonBox,
    QMessageBox,
)
from qgis.PyQt import uic
from qgis.core import (
    QgsMapLayerProxyModel,
    QgsVectorLayer,
    QgsProcessingFeedback,
    QgsFields,
)


from .results.charts import SituationChart
from .dataclasses import ScenarioGBProperties, ScenarioResult
from .widgets.completer_combobox_widget import CompleterComboBox
from .helpers.helpers import (
    get_distinct_attributes_values_from_layer,
    input_vector_validator,
    path_validator,
    vector_layer_field_is_numeric,
)
from .results.widgets.scenarios_result_viewer_widget.scenarios_results_viewer_widget import (
    ScenariosResultViewerWidget,
)
from ..helpers.input_layer_file_widget import InputLayerFileWidget
from ..helpers.custom_logger import CustomLogger
from ...helpers.helpers import run_command, get_console_command

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(Path(__file__).parent / "ui" / "scenarios_gb_dialog.ui")


class ScenariosGBDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """constructor"""
        super(ScenariosGBDialog, self).__init__(parent)
        QgsProcessingFeedback.__init__(self)

        self._parent = parent
        self.input_bocage_raster_layer_selector: InputLayerFileWidget
        self.input_exploitation_vector_layer_selector: InputLayerFileWidget
        self.input_amenagements_vector_layer_selector: InputLayerFileWidget
        self.id_exploitation_combobox: CompleterComboBox
        self._logger: CustomLogger
        self.results_viewer_tab = ScenariosResultViewerWidget(self)
        self.results: list[ScenarioResult] = []

        # Setup Ui
        self.setupUi(self)
        self.setup_gui()
        self.pushButton_run = QPushButton("Run")
        self.button_box.addButton(self.pushButton_run, QDialogButtonBox.ActionRole)
        self.pushButton_run.clicked.connect(self.run_scenario)

    def setup_gui(self) -> None:
        """setup gui widget properties"""
        self.setup_definition_exploitation_gui()
        self.setup_definition_bocage_gui()
        self.setup_amenagements_gui()
        self.setup_results_viewer_tab()
        self.setup_logger()

    def setup_logger(self) -> None:
        self._logger = CustomLogger(self.textEdit_journal, self.progressBar)
        self.pushButton_interrupt.clicked.connect(self.cancel_command)

    def setup_definition_exploitation_gui(self) -> None:
        """setup gui widget properties"""
        self.input_exploitation_vector_layer_selector = InputLayerFileWidget(self)
        self.input_exploitation_vector_layer_selector.setFilters(
            QgsMapLayerProxyModel.VectorLayer
        )
        self.groupBox_definition_exploitation.layout().addWidget(
            self.input_exploitation_vector_layer_selector, 0, 1
        )
        self.input_exploitation_vector_layer_selector.setComboboxIndex(-1)

        # create commune completer combobox and add it to the layout
        self.id_exploitation_combobox = CompleterComboBox()

        self.groupBox_definition_exploitation.layout().addWidget(
            self.id_exploitation_combobox, 2, 1
        )
        self.input_exploitation_vector_layer_selector.mlcb.layerChanged.connect(
            self.on_input_exploitation_layer_changed
        )
        self.mFieldComboBox_exploitation_id_field.fieldChanged.connect(
            self.on_exploitation_id_field_changed
        )

    def setup_definition_bocage_gui(self) -> None:
        """setup gui widget properties"""
        self.input_bocage_raster_layer_selector = InputLayerFileWidget(self)
        self.input_bocage_raster_layer_selector.setFilters(
            QgsMapLayerProxyModel.RasterLayer
        )
        self.groupBox_MNHC.layout().addWidget(
            self.input_bocage_raster_layer_selector, 0, 0
        )
        self.input_bocage_raster_layer_selector.setComboboxIndex(-1)

    def setup_amenagements_gui(self) -> None:
        """setup gui widget properties"""

        self.lineEdit_resultPrefix.setText("initial")
        self.input_amenagements_vector_layer_selector = InputLayerFileWidget(self)
        self.input_amenagements_vector_layer_selector.setFilters(
            QgsMapLayerProxyModel.VectorLayer
        )
        self.groupBox_amenagements.layout().addWidget(
            self.input_amenagements_vector_layer_selector, 1, 1
        )
        self.input_amenagements_vector_layer_selector.setComboboxIndex(-1)

        self.input_amenagements_vector_layer_selector.mlcb.layerChanged.connect(
            self.on_input_amenagement_layer_changed
        )
        self.mFieldComboBox_scenarios.fieldChanged.connect(
            self.on_amenagement_scenario_field_changed
        )
        self.radioButton_scenario.toggled.connect(self.on_scenario_radio_button_clicked)
        self.radioButton_initial.toggled.connect(self.on_initial_radio_button_clicked)

        self.radioButton_initial.setChecked(True)
        self.on_scenario_radio_button_clicked()

    def on_scenario_radio_button_clicked(self) -> None:
        """scenario radio button clicked action"""
        self.groupBox_amenagements.setEnabled(self.radioButton_scenario.isChecked())

    def on_initial_radio_button_clicked(self) -> None:
        """initial radio button clicked action"""
        self.lineEdit_resultPrefix.setText("initial")

    def setup_results_viewer_tab(self) -> None:
        """setup exploitation situation result viewer"""
        self.gridLayout_result_viewer.addWidget(self.results_viewer_tab)
        self.mQgsFileWidget_result_directory_selector.fileChanged.connect(
            self.on_result_directory_changed
        )

    def on_input_exploitation_layer_changed(self) -> None:
        """input exploitation layer changed action"""
        self.mFieldComboBox_exploitation_id_field.clear()
        self.id_exploitation_combobox.clear()
        current_layer: QgsVectorLayer = (
            self.input_exploitation_vector_layer_selector.currentLayer()
        )
        self.mFieldComboBox_exploitation_id_field.setLayer(current_layer)
        fields: QgsFields = self.mFieldComboBox_exploitation_id_field.fields()
        # force reset field because it is not updated when layer is changed in the InputLayerFileWidget if the user select the layer from the select file dialog
        self.mFieldComboBox_exploitation_id_field.setFields(fields)
        self.mFieldComboBox_exploitation_id_field.setCurrentIndex(0)

    def on_exploitation_id_field_changed(self) -> None:
        """exploitation id field changed action"""

        self.id_exploitation_combobox.clear()

        id_exploitations: list[str] = get_distinct_attributes_values_from_layer(
            self.input_exploitation_vector_layer_selector.currentLayer(),
            self.mFieldComboBox_exploitation_id_field.currentField(),
        )
        self.id_exploitation_combobox.addItems(id_exploitations)

    def on_input_amenagement_layer_changed(self) -> None:
        """input amenagement layer changed action"""
        # check if the layer has a at least a field name "initial" that is a numeric field
        self.mFieldComboBox_scenarios.clear()
        selected_layer: QgsVectorLayer = (
            self.input_amenagements_vector_layer_selector.currentLayer()
        )
        self.mFieldComboBox_scenarios.setLayer(selected_layer)
        fields: QgsFields = self.mFieldComboBox_scenarios.fields()
        # force reset field because it is not updated when layer is changed in the InputLayerFileWidget if the user select the layer from the select file dialog
        self.mFieldComboBox_scenarios.setFields(fields)
        self.mFieldComboBox_scenarios.setCurrentIndex(0)
        self.lineEdit_resultPrefix.setText("")

    def on_amenagement_scenario_field_changed(self) -> None:
        """amenagement scenario field changed action"""
        # check if the select field is a number field
        selected_layer: QgsVectorLayer = (
            self.input_amenagements_vector_layer_selector.currentLayer()
        )
        selected_field: str = self.mFieldComboBox_scenarios.currentField()
        if not vector_layer_field_is_numeric(selected_layer, selected_field):
            self.mFieldComboBox_scenarios.setCurrentIndex(-1)
            self.lineEdit_resultPrefix.setText("")
            return
        self.lineEdit_resultPrefix.setText(f"{selected_field}")
        # if not, show an error message and set the index to -1

    def check_mandatory_inputs(self) -> bool:
        """Inputs validation. Checks if mandatory inputs are valid values"""
        # input exploitation layer must be set and valid path

        if not input_vector_validator(
            "couche exploitation",
            Path(self.input_exploitation_vector_layer_selector.currentFilePath()),
        ):
            return False
        # input exploitation id field must be set
        if self.mFieldComboBox_exploitation_id_field.currentIndex() == -1:
            QMessageBox.warning(
                self,
                "Erreur",
                "Le champ identifiant exploitation doit être choisi",
            )
            return False
        # id exploitation combobox must be set
        if self.id_exploitation_combobox.currentIndex() == -1:
            QMessageBox.warning(
                self,
                "Erreur",
                "L'identifiant exploitation doit être choisi",
            )
            return False
        # input bocage raster layer must be set and valid path
        if not path_validator(
            "Couche bocage",
            "couche raster bocage",
            Path(self.input_bocage_raster_layer_selector.currentFilePath()),
        ):
            return False
        # if amenagements radio button is checked, input aménagements layer must be set and valid path
        if self.radioButton_scenario.isChecked():
            if not input_vector_validator(
                "couche aménagements",
                Path(self.input_amenagements_vector_layer_selector.currentFilePath()),
            ):
                return False
            if self.mFieldComboBox_scenarios.currentIndex() == -1:
                QMessageBox.warning(
                    self,
                    "Couche aménagements",
                    "Le champ scenario dans l'onglet Aménagements doit être choisi",
                )
                return False
        # output folder must be set and valid path
        if not path_validator(
            "Dossier de sortie",
            "dossier de sortie",
            Path(self.mQgsFileWidget_resultDir.filePath()),
        ):
            return False
        # lineEdit_resultPrefix must be set et not empty
        if self.lineEdit_resultPrefix.text() == "":
            QMessageBox.warning(
                self,
                "Erreur",
                "Le nom du scénario dans l'onglet Sorties doit être choisi",
            )
            return False
        return True

    def properties_factory(self, scenario_name_input: str) -> ScenarioGBProperties:
        """create properties file"""
        return ScenarioGBProperties(
            scenario_name=scenario_name_input,
            parcellaire=Path(
                rf"{self._input_exploitation_vector_layer_selector.currentFilePath()}"
            ),
            attribut_code_ea=self.mFieldComboBox_exploitation_id_field.currentField(),
            code_ea=self._id_exploitation_combobox.currentText(),
            bocage=Path(
                rf"{self._input_bocage_raster_layer_selector.currentFilePath()}"
            ),
            # conditional value for amenagement
            amenagement=(
                Path(
                    rf"{self._input_amenagements_vector_layer_selector.currentFilePath()}"
                )
                if self.radioButton_scenario.isChecked()
                else Path()
            ),
            attribut_scenario=self.mFieldComboBox_scenarios.currentField(),
            output_folder=Path(rf"{self.mQgsFileWidget_resultDir.filePath()}"),
            grain_bocager_cellsize=self.doubleSpinBox_pixelSize.value(),
            grain_bocager_window_radius=self.spinBox_radius.value(),
            grain_bocager_thresholds=[
                self.doubleSpinBox_seuilFonctionnel.value(),
                self.doubleSpinBox_seuilPotentiel.value(),
                self.doubleSpinBox_seuilOuvert.value(),
            ],
        )

    def run_scenario(self) -> None:
        if not self.check_mandatory_inputs():
            return
        # run grain bocager
        self.tabWidget.setCurrentIndex(5)
        self.tab_journal.show()
        self.tab_journal.update()
        self.tab_journal.repaint()

        # create properties file from parameters
        scenario_name_input: str = self.lineEdit_resultPrefix.text()
        properties: ScenarioGBProperties = self.properties_factory(scenario_name_input)
        properties.create_properties_file()
        file_path: Path = properties.get_properties_file_path()
        command: str = get_console_command(str(file_path))
        # run process with properties file

        run_command(command_line=command, feedback=self._logger)
        # wait for process to finish
        self.mQgsFileWidget_result_directory_selector.setFilePath(
            self.mQgsFileWidget_resultDir.filePath()
        )
        # if the result directory did not change
        if (
            self.mQgsFileWidget_resultDir.filePath()
            == self.mQgsFileWidget_result_directory_selector.filePath()
        ):
            self.results_viewer_tab.update_results()

    def on_result_directory_changed(self) -> None:
        """on result directory changed"""
        self.results_viewer_tab.set_result_directory_path(
            Path(self.mQgsFileWidget_result_directory_selector.filePath())
        )

        if self.id_exploitation_combobox.currentIndex() > -1:
            self.results_viewer_tab.set_selected_exploitation_id(
                self.id_exploitation_combobox.currentText()
            )

    def cancel_command(self) -> None:
        self._logger.set_is_canceled(True)
