# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Tuple

from qgis.core import (
    QgsRasterLayer,
    QgsProcessing,
    QgsProcessingParameterMultipleLayers,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterMatrix,
    QgsExpressionContext,
    QgsExpressionContextScope,
    QgsProcessingContext,
)

from processing.tools.system import isWindows

from ..chloe_algorithm import ChloeAlgorithm
from ..helpers.constants import INPUTS_MATRIX, DOMAINS, OUTPUT_RASTER, SAVE_PROPERTIES
from ...gui.custom_parameters.chloe_raster_parameter_file_destination import (
    ChloeRasterParameterFileDestination,
)
from ...helpers.helpers import (
    format_path_for_properties_file,
)
from ...gui.custom_widgets.constants import CUSTOM_WIDGET_DIRECTORY
from ...gui.custom_widgets.factor_table.dataclasses import CombineFactorElement


class CombineAlgorithm(ChloeAlgorithm):
    """
    Algorithm combine
    """

    def __init__(self):
        super().__init__()

        self.combination_formula: str = ""
        self.combine_factor_elements: list[CombineFactorElement] = []
        self.output_raster: str = ""

    def initAlgorithm(self, config=None):
        self.init_input_params()
        self.init_algorithm_params()
        self.init_output_params()

    def init_input_params(self):
        """Init input parameters."""
        # === INPUT PARAMETERS ===

        # INPUT MATRIX
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                INPUTS_MATRIX, self.tr("Input rasters"), QgsProcessing.TypeRaster
            )
        )

    def init_algorithm_params(self):
        """Init algorithm parameters."""
        # COMBINE EXPRESSION
        combine_parameter = QgsProcessingParameterMatrix(
            name=DOMAINS, description=self.tr("Combination"), defaultValue=""
        )
        combine_parameter.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.factor_table.widget_wrapper.ChloeFactorTableWidgetWrapper",
                    "input_matrix_param_name": INPUTS_MATRIX,
                    "parentWidgetConfig": {
                        "linkedParams": [
                            {
                                "paramName": INPUTS_MATRIX,
                                "refreshMethod": "refresh_factor_table",
                            },
                        ]
                    },
                }
            }
        )

        self.addParameter(combine_parameter)

    def init_output_params(self):
        """Init output parameters."""
        # === OUTPUT PARAMETERS ===

        # Output Asc
        output_raster_parameter = ChloeRasterParameterFileDestination(
            name=OUTPUT_RASTER, description=self.tr("Output Raster")
        )

        self.addParameter(output_raster_parameter, createOutput=True)

        # Properties file
        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=SAVE_PROPERTIES,
                description=self.tr("Properties file"),
                fileFilter="Properties (*.properties)",
            )
        )

    def name(self):
        return "combine"

    def displayName(self):
        return self.tr("Combine")

    def group(self):
        return self.tr("util")

    def groupId(self):
        return "util"

    def commandName(self):
        return "combine"

    def replace_combine_factor_element_empty_layer_path(
        self,
        factors: list[CombineFactorElement],
        scoped_raster_layers: list[Tuple[QgsRasterLayer, str]],
    ) -> list[CombineFactorElement]:
        """
        Replaces the empty Path provided by the domain parameter in MODELER mode by the raster layers in context.

        Args:
            factors (list[CombineFactorElement]): List of CombineFactorElement objects.
            scoped_raster_layers (list[Tuple[QgsRasterLayer, str]]): List of tuples containing QgsRasterLayer and input name.

        Returns:
            list[CombineFactorElement]: List of updated CombineFactorElement objects.
        """
        # print(factors)
        # print(scoped_raster_layers)
        updated_factors: list[CombineFactorElement] = []
        # Loop through each factor
        for factor in factors:
            # If the factor's layer path is empty, search for the corresponding layer in the scoped raster_layers list
            if factor.layer_path == Path():
                for raster_layer, input_name in scoped_raster_layers:
                    if factor.layer_id == input_name:
                        factor.layer_path = Path(raster_layer.source())

            updated_factors.append(factor)

        return updated_factors

    def get_raster_layers_in_algorithm_inputs_scope(
        self, context: QgsExpressionContext
    ) -> list[Tuple[QgsRasterLayer, str]]:
        """
        # TODO : move this method to helpers if needed in other algorithms
        Returns a list of tuples containing QgsRasterLayer and variable names that are in the scope of the algorithm_inputs
        expression context.

        Args:
            context (QgsExpressionContext): The expression context to search for scoped layers.

        Returns:
            list[Tuple[QgsRasterLayer, str]]: A list of tuples containing QgsRasterLayer and variable names that are in the
            scope of the algorithm_inputs expression context.
        """
        scope_layer_list: list[Tuple[QgsRasterLayer, str]] = []

        index_of_scope: int = context.expressionContext().indexOfScope(
            "algorithm_inputs"
        )

        # if the scope is found
        if index_of_scope >= 0:
            expression_context_alg_inputs_scope: QgsExpressionContextScope = (
                context.expressionContext().scope(index_of_scope)
            )
            for variable_name in expression_context_alg_inputs_scope.variableNames():
                layer_in_context = expression_context_alg_inputs_scope.variable(
                    variable_name
                )
                if isinstance(layer_in_context, QgsRasterLayer):
                    scope_layer_list.append((layer_in_context, variable_name))

        return scope_layer_list

    def set_properties_algorithm_values(self, parameters, context, feedback) -> None:
        """Set algorithm parameters."""

        """input_factors as returned by parameterAsMatrix is a list of two elements (only lists are supported in the modeler model3 file) :
        - the first element is a list of CombineFactorElement objects or lists of strings wich are representing a CombineFactorElement as list (strings are used in the modeler context because of the model3 file)
        - the second element is a string representing the combination formula
        """

        input_factors: "list[list[CombineFactorElement|list[str]] | str]" = (
            self.parameterAsMatrix(parameters, DOMAINS, context)
        )

        if not input_factors:
            feedback.reportError("Domain values are invalid")
            return

        self.set_combine_factor_elements(input_factors[0], context)

        self.combination_formula = input_factors[1]

    def set_combine_factor_elements(
        self, input_factors: "list[CombineFactorElement | list[str]]", context
    ) -> None:
        """
        Set self.combine_factor_elements based on execution context.

        Args:
            input_factors (list[CombineFactorElement | str]): List of CombineFactorElements or lists of strings (strings are used in the modeler context because of the model3 file).
            context: QgsProcessingContext object.

        Returns:
            None
        """

        rasters_layers_in_context = self.get_raster_layers_in_algorithm_inputs_scope(
            context=context
        )

        # convert input factors to CombineFactorElement objects when factors are coming from the modeler (as strings)
        converted_input_factors = [
            CombineFactorElement.from_string(factor)
            if not isinstance(factor, CombineFactorElement)
            else factor
            for factor in input_factors
        ]

        self.combine_factor_elements = (
            self.replace_combine_factor_element_empty_layer_path(
                converted_input_factors, rasters_layers_in_context
            )
        )

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""
        self.output_raster = self.parameterAsOutputLayer(
            parameters, OUTPUT_RASTER, context
        )
        self.create_projection_file(output_path_raster=Path(self.output_raster))
        self.set_output_parameter_value(OUTPUT_RASTER, self.output_raster)

        # === SAVE_PROPERTIES

        f_save_properties = self.parameterAsString(parameters, SAVE_PROPERTIES, context)

        self.set_output_parameter_value(SAVE_PROPERTIES, f_save_properties)

    def set_properties_values(self, parameters, context, feedback):
        """set properties values."""
        self.set_properties_algorithm_values(parameters, context, feedback)

        self.set_properties_output_values(parameters, context, feedback)

    def get_properties_lines(self) -> list[str]:
        """get properties lines."""
        properties_lines: list[str] = []

        properties_lines.append("treatment=combine")
        properties_lines.append(f"combination={self.combination_formula}")

        factors: str = ";".join(
            [
                f"({factor.layer_path},{factor.factor_name})"
                for factor in self.combine_factor_elements
            ]
        )
        properties_lines.append(
            format_path_for_properties_file(f"factors={{{factors}}}", isWindows())
        )
        properties_lines.append(
            format_path_for_properties_file(
                input_string=f"output_raster={self.output_raster}",
                is_windows_system=isWindows(),
            )
        )
        return properties_lines
