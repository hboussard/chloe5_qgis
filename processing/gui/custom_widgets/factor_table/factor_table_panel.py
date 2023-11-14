# -*- coding: utf-8 -*-

"""
*********************************************************************************************
    factor_table_panel.py
    ---------------------

        Widget used in the Combine Algorithm. Sets the input rasters names and setup the combination formula.
        Date                 : May 2019

        email                : daan.guillerme at fdc22.com / hugues.boussard at inra.fr
*********************************************************************************************

"""

# This will get replaced with a git SHA1 when you do a git archive

from pathlib import Path
from typing import Union


from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QMessageBox, QHeaderView


from qgis.core import QgsProcessingParameterDefinition, QgsMessageLog, Qgis
from processing.gui.BatchPanel import BatchPanel
from processing.gui.wrappers import DIALOG_MODELER, DIALOG_STANDARD, DIALOG_BATCH
from .....helpers.helpers import get_layer_name
from ....algorithms.helpers.constants import INPUTS_MATRIX
from ....gui.chloe_algorithm_dialog import ChloeParametersPanel
from ..helpers import (
    extract_raster_layer_path,
    get_param_wrappers_from_algorithm_dialog,
    get_parameter_value_from_batch_standard_algorithm_dialog,
    get_parameter_widget_wrapper_from_batch_panel,
)
from .dataclasses import CombineFactorElement, LayerInfo
from .models import FactorTableModel


WIDGET, BASE = uic.loadUiType(Path(__file__).resolve().parent / "WgtCombineSelector.ui")


class FactorTablePanel(BASE, WIDGET):
    """
    A widget containing a table view to edit raster combinations.

    Attributes:
        parent (QgsProcessingAlgorithmDialog): The parent dialog.
        input_matrix_parameter_name (str): The name of the input matrix parameter.
        dialog_type (int): The dialog type (standard or modeler).
        is_modeler_dialog (bool): Whether the dialog is in modeler mode.
        _table_model (FactorTableModel): The table model.
    """

    def __init__(
        self,
        parent,
        input_matrix_parameter_name: str = INPUTS_MATRIX,
        dialog_type=DIALOG_STANDARD,
    ):
        """
        Args:
            input_matrix (str): The name of the input matrix parameter.
            dialog_type (int): The dialog type (standard or modeler).
        """

        super(FactorTablePanel, self).__init__(None)
        self.setupUi(self)
        self.parent_dialog = parent
        self.input_matrix_parameter_name: str = input_matrix_parameter_name
        self.dialog_type: str = dialog_type

        # Determine whether the dialog is in modeler mode.
        self.is_modeler_dialog: bool = False
        if self.dialog_type == DIALOG_MODELER:
            self.is_modeler_dialog = True

        self.init_gui()

    def init_gui(self) -> None:
        """Initializes the GUI."""
        # Create and set the table model.
        self._table_model: FactorTableModel = FactorTableModel()
        self.tableView.setModel(self._table_model)
        self.tableView.setColumnHidden(3, True)

        # Set column sizes.
        # Set column 0 to match header text
        self.tableView.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        # Set column 1 to match column content
        self.tableView.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        # Set column 2 to stretch to the remaining space
        self.tableView.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        # Set the placeholder text for the combination formula text box.
        self.LineEdit_formula.setPlaceholderText(self.tr("Combination Formula"))

        # Connect the populate button to the populateTableModel method.
        self.button_load_layers.clicked.connect(self.populate_table_model)

    def populate_table_model(self) -> None:
        """Populates the table model."""
        if self.is_modeler_dialog:
            list_layers: list[LayerInfo] = self.get_list_layers_for_modeler()
        else:
            list_layers = self.get_list_layers_for_standard_batch()

        self.populate_table_model_with_data(list_layers=list_layers)

    def get_list_layers_for_modeler(self) -> list[LayerInfo]:
        """
        Get a list of tuples representing the input layers from the INPUTS_MATRIX parameter in modeler dialog.

        Each tuple contains a layer name and a layer ID. The layer ID is generated based on the type of input layer:
        - If the layer is a modeler input, the ID is the name of the input parameter.
        - If the layer is an algorithm output, the ID is a combination of the algorithm display name and the selected output name.

        Returns:
            A list of tuples, where each tuple contains a layer name and a layer ID.
        """
        # Initialize an empty list to hold layer names and IDs
        list_layers: list[LayerInfo] = []

        # TODO : Accessing the modeler widget that way is a bit hacky, find a better way to do this
        modeler_widget = get_param_wrappers_from_algorithm_dialog(
            algorithm_dialog=self.parent_dialog, dialog_type=DIALOG_MODELER
        )[self.input_matrix_parameter_name]
        if modeler_widget is None or not isinstance(modeler_widget.value(), list):
            error_message: str = self.tr("Error: no modeler wrapper found")
            QgsMessageLog.logMessage(error_message, level=Qgis.Critical)
            return list_layers

        # Iterate over the values of the INPUTS_MATRIX widgets in the dialog
        for value in modeler_widget.value():
            # Get the path of the layer
            layer_path: str = self.parent_dialog.resolveValueDescription(value)
            # Initialize layer_id to an empty string
            layer_id: str = ""
            # Get the algorithm child id of the current layer to check if it is a algorithm output
            value_algorithm_child_id: str = value.outputChildId()

            # Check if the current layer is a modeler input
            is_modeler_input: bool = False
            if isinstance(
                self.parent_dialog.model.parameterDefinition(value.parameterName()),
                QgsProcessingParameterDefinition,
            ):
                is_modeler_input = True
                # If it is, set layer_id to the name of the input parameter
                layer_id = self.parent_dialog.model.parameterDefinition(
                    value.parameterName()
                ).name()

            # Check if the current layer is an algorithm output
            if value_algorithm_child_id:
                # TODO : this is a bit hacky, maybe there is a better way to do this
                # If it is, get the algorithm associated with the output and generate a unique layer ID
                alg = self.parent_dialog.model.childAlgorithm(value_algorithm_child_id)
                # the layer ID is a combination of the algorithm display name and the selected output name
                # this string is the same than the one generated by context.expressionContext().indexOfScope("algorithm_inputs") in the algorithm post process. Allows the matching of the layers in the processAlgorithm
                layer_id = f'{alg.algorithm().displayName().replace(" ", "_")}_{value.outputName()}'
            list_layers.append(
                LayerInfo(
                    layer_path=layer_path
                    if is_modeler_input
                    else extract_raster_layer_path(layer_path),
                    modeler_input_id=layer_id,
                )
            )
        return list_layers

    def get_list_layers_for_standard_batch(self) -> list[LayerInfo]:
        """
        Get a list of tuples representing the input layers from the INPUTS_MATRIX parameter in standard or batch dialog.

        Each tuple contains a layer name and an empty layer ID.

        Returns:
            A list of tuples, where each tuple contains a layer name and an empty layer ID.
        """
        list_layers: list[LayerInfo] = []

        widget_values = get_parameter_value_from_batch_standard_algorithm_dialog(
            dialog_type=self.dialog_type,
            param_name=self.input_matrix_parameter_name,
            algorithm_dialog=self.parent_dialog,
        )
        if widget_values is None:
            return list_layers

        for val in widget_values:
            # in standard mode no need to provide a modeler_input_id
            list_layers.append(
                LayerInfo(
                    layer_path=extract_raster_layer_path(val), modeler_input_id=""
                )
            )

        return list_layers

    def populate_table_model_with_data(self, list_layers: list[LayerInfo]) -> None:
        """
        Populates the table model with data based on the given list of layers.

        Args:
            list_layers: A list of tuples, where each tuple contains a layer name (str) and a layer ID (str).

        Returns:
            None.
        """
        factor_elements: list[CombineFactorElement] = []

        # If the list of layers is empty, show an error message and return.
        if not list_layers:
            QMessageBox.critical(
                self, self.tr("Select rasters"), self.tr("No rasters selected")
            )
            return
        else:
            # For each layer in the list of layers, create a CombineFactorElement object and append it to the factor_elements list.
            for i, layer in enumerate(list_layers):
                if self.is_modeler_dialog:
                    # if the layer id is not empty, it means that the layer is a modeler input, set the path to an empty string. It will be resolved in the processAlgorithm
                    if layer.modeler_input_id != "":
                        layer_name = layer.layer_path
                        layer_path: str = ""
                    # if the layer id is empty, it means that the layer is a selected layer. Set the path to the actual path of the layer
                    else:
                        layer_name: str = get_layer_name(layer.layer_path)
                        layer_path = layer.layer_path
                else:
                    layer_name = get_layer_name(layer.layer_path)
                    layer_path = layer.layer_path

                factor_elements.append(
                    CombineFactorElement(
                        factor_name=f"m{i+1}",
                        layer_name=layer_name,
                        layer_path=Path(layer_path),
                        layer_id=layer.modeler_input_id,
                    ),
                )

        self._table_model.set_data(data=factor_elements)

    def value(self) -> "list[list[CombineFactorElement | list[str]] | str] | None":
        """
        Returns a list of CombineFactorElements representing the selected rasters, and the combination formula
        entered by the user. Returns None if the input is not valid.

        in case of modeler the value is a list of list of strings because the values are stored in the model xml file as a list of strings
        """

        # Check if the table model exists
        if self._table_model is None:
            return

        # Check for empty factor names and column duplicates
        if (
            self._table_model.has_empty_layer_names()
            or self._table_model.has_column_duplicates()
        ):
            return

        # Check for a valid formula
        formula = self.LineEdit_formula.text()
        if not formula or not self.formula_is_valid(formula):
            return

        # Return the list of factor elements and the formula
        return_list = [
            self._table_model.get_combine_factor_elements(self.is_modeler_dialog),
            formula,
        ]
        return return_list

    def formula_is_valid(self, formula: str) -> bool:
        if formula is None or formula == "":
            return False
        return True

    def setValue(self, value: "list[list[CombineFactorElement] | str]") -> None:
        """
        Set the value of the CombineTable and formula line edit.

        Args:
            value (list[list[CombineFactorElement] |str]): A list of lists, where each inner list is a list of
                CombineFactorElement objects, and a string formula, representing the current value of the widget.

            the first element should always be the list o CombineFactorElement, and the second one the formula.
            This order is constraint by the way the value is stored in the model xml file
        """
        if value and len(value) > 1:
            self.LineEdit_formula.setText(str(value[1]))
            self._table_model.set_data(value[0])
