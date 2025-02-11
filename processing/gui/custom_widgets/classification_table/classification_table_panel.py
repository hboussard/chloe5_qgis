from pathlib import Path
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QHeaderView
from .....helpers.helpers import get_unique_raster_values
from ..helpers import get_input_raster_param_path
from .models import ClassificationTableModel
from .delegates import DomainValueDelegate, ClassificationModelIntValueDelegate


WIDGET, BASE = uic.loadUiType(
    Path(__file__).resolve().parent / "DlgClassificationTableInput.ui"
)


class ClassificationTablePanel(BASE, WIDGET):
    def __init__(self, parent, dialog_type: str, input_raster_param_name: str):
        super(ClassificationTablePanel, self).__init__(None)
        self.setupUi(self)
        self.algorithm_dialog = parent
        self.dialog_type: str = dialog_type
        self.input_raster_param_name = input_raster_param_name
        self.input_raster_values: list[float] = []

        self._table_model: ClassificationTableModel = ClassificationTableModel()

        self.pushButton_add_tableview_row.clicked.connect(self.add_table_row)
        self.pushButton_delete_tableview_row.clicked.connect(self.remove_table_row)
        self.pushButton_validate_domains.clicked.connect(self.validate_domains)

        self._table_model.signal_model_updated.connect(self.update_propertie_value)
        # self._table_model.signal_model_updated.connect(self.check_domains)

        self.init_gui()

    def init_gui(self):
        self.lineEdit_domains.setPlaceholderText("(Domain1-class1);(Domain2-class2)")

        self.tableView_classification.setModel(self._table_model)
        self.tableView_classification.setItemDelegateForColumn(
            0, DomainValueDelegate(self.tableView_classification)
        )
        self.tableView_classification.setItemDelegateForColumn(
            1, ClassificationModelIntValueDelegate(self.tableView_classification)
        )
        #  Set columns to stretch to the remaining space
        self.tableView_classification.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.label_domain_warning.setVisible(False)

    def add_table_row(self) -> None:
        """Add a row to the mapping table"""
        self._table_model.appendRow([None, None])

    def remove_table_row(self) -> None:
        """Remove a row from the mapping table"""
        self._table_model.removeRow(self.tableView_classification.currentIndex().row())

    def update_propertie_value(self):
        """Update le text"""
        self.lineEdit_domains.setText(self._table_model.get_data_as_propertie_list())

    def set_raster_values(self) -> None:
        """Set the raster values reference from the input raster file.

        This method retrieves the unique raster values from the input raster file
        and assigns them to the `input_raster_values` attribute of the class.

        Returns:
            None
        """

        self.input_raster_values = get_unique_raster_values(
            raster_file_path=get_input_raster_param_path(
                dialog_type=self.dialog_type,
                input_raster_layer_param_name=self.input_raster_param_name,
                algorithm_dialog=self.algorithm_dialog,
            )
        )

    def reset_domain_validation(self):
        """Reset the domain warning label."""
        self.input_raster_values = []
        self.label_domain_warning.setText("")
        self.label_domain_warning.setVisible(False)

    def validate_domains(self):
        """Validate the domains in the classification table."""
        # only trigger set_raster_values if the input_raster_values are not already set
        if not self.input_raster_values:
            self.set_raster_values()
        self.check_domains()

    def check_domains(self):
        """
        Check the domains of the raster values.

        This function retrieves the unique raster values from the input raster file and checks if they are covered by the domains defined in the classification table.
        If any raster values are not covered by the domains, a warning message is displayed.

        Returns:
            None
        """

        if not self.input_raster_values:
            return

        values_not_covered: list[float] = (
            self._table_model.values_not_contained_in_domains(self.input_raster_values)
        )

        if values_not_covered:
            # log warning to the log label
            self.label_domain_warning.setVisible(True)
            self.label_domain_warning.setText(
                f"All raster input values are not contained in the domains ({min(self.input_raster_values)} - {max(self.input_raster_values)})"
            )
            # set text in orange
            self.label_domain_warning.setStyleSheet("color: orange;")
        else:
            self.label_domain_warning.setVisible(False)

    def value(self) -> "list[list[list[str]] | str]":
        """
        Get the value of the classification table panel.
        The returned value is a list of list of list of strings (the domains with the mapped class value) or a string (the propertie string).
        This type of value is used so that the widget can also be used in the modeler mode.
        Returns:
            list[list[list[str]] | str]: The value of the classification table panel.
        """
        return [
            self.lineEdit_domains.text(),
            self._table_model.get_data(),
        ]

    def setValue(self, value: "list[list[list[str]] | str]"):
        """
        Sets the value of the classification table panel.

        Args:
            value (list[list[list[str]] | str]): The value to be set. It should be a nested list of strings (domains/class) and a single string in second position (propertie string ).
            This type of value is used so that the widget can also be used in the modeler mode.
        Returns:
            None
        """
        if value and len(value) > 1:
            self._table_model.set_data(value[1])
            self.lineEdit_domains.setText(str(value[0]))
