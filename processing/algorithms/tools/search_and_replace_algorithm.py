# -*- coding: utf-8 -*-

import os
from pathlib import Path

from qgis.core import (
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows

from ...gui.custom_widgets.constants import CUSTOM_WIDGET_DIRECTORY
from ...gui.custom_parameters.chloe_raster_parameter_file_input import (
    ChloeRasterParameterFileInput,
)
from ...gui.custom_parameters.chloe_raster_parameter_file_destination import (
    ChloeRasterParameterFileDestination,
)
from ...helpers.helpers import (
    format_path_for_properties_file,
)
from ..helpers.constants import (
    INPUT_RASTER,
    OUTPUT_RASTER,
    SAVE_PROPERTIES,
    NODATA_VALUE,
    UTILS_GROUP_ID,
    UTILS_GROUP_NAME,
    VALUES_MAPPING,
    MAP_CSV,
)

# Mother class
from ..chloe_algorithm import ChloeAlgorithm


class SearchAndReplaceAlgorithm(ChloeAlgorithm):
    """
    Algorithm search and replace
    """

    def __init__(self):
        super().__init__()

        # properties values
        self.input_raster_layer: str = ""
        self.output_raster_layer: str = ""
        self.changes: str = ""
        self.nodata_value: str = ""

    def initAlgorithm(self, config=None):
        self.init_input_params()
        self.init_algorithm_params()
        self.init_output_params()

    def init_input_params(self):
        """Init input parameters."""
        # === INPUT PARAMETERS ===

        input_raster_param = ChloeRasterParameterFileInput(
            name=INPUT_RASTER, description=self.tr("Input raster layer")
        )
        input_raster_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.raster_input.widget_wrapper.ChloeAscRasterWidgetWrapper"
                }
            }
        )
        self.addParameter(input_raster_param)

    def init_algorithm_params(self):
        """Init algorithm parameters."""
        # MAP CSV
        csv_file_param = QgsProcessingParameterFile(
            name=MAP_CSV,
            description=self.tr("CSV Map"),
            optional=True,
        )
        csv_file_param.setFileFilter("CSV files (*.csv);;Text files (*.txt)")

        self.addParameter(csv_file_param)

        # CHANGES
        mapping_values_param = QgsProcessingParameterString(
            name=VALUES_MAPPING,
            description=self.tr("Values to search and replace"),
            defaultValue="",
        )
        mapping_values_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.mapping_table.widget_wrapper.ChloeMappingTableWidgetWrapper",
                    "input_raster_layer_param_name": INPUT_RASTER,
                    "parent_widget_config": {
                        "linked_parameters": [
                            {
                                "parameter_name": MAP_CSV,
                                "action": "populate_csv_mapping_combobox",
                            },
                            {
                                "parameter_name": INPUT_RASTER,
                                "action": "clear_mapping_table",
                            },
                        ]
                    },
                }
            }
        )
        self.addParameter(mapping_values_param)

        # NO DATA VALUE
        self.addParameter(
            QgsProcessingParameterNumber(
                name=NODATA_VALUE,
                description=self.tr("Nodata value"),
                defaultValue=-1,
            )
        )

    def init_output_params(self):
        """Init output parameters."""
        # === OUTPUT PARAMETERS ===

        raster_output_parameter = ChloeRasterParameterFileDestination(
            name=OUTPUT_RASTER,
            description=self.tr("Output Raster"),
        )

        self.addParameter(raster_output_parameter)

        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=SAVE_PROPERTIES,
                description=self.tr("Properties file"),
                fileFilter="Properties (*.properties)",
            )
        )

    def name(self):
        return "search and replace"

    def displayName(self):
        return self.tr("search and replace")

    def group(self):
        return self.tr(UTILS_GROUP_NAME)

    def groupId(self):
        return UTILS_GROUP_ID

    def commandName(self):
        return "search and replace"

    def set_properties_input_values(self, parameters, context, feedback):
        """Set input values."""
        self.input_raster_layer = self.parameterRasterAsFilePath(
            parameters, INPUT_RASTER, context
        )

    def set_properties_algorithm_values(self, parameters, context, feedback):
        """Set algorithm parameters."""
        self.changes = self.parameterAsString(parameters, VALUES_MAPPING, context)
        self.nodata_value = self.parameterAsString(parameters, NODATA_VALUE, context)

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""
        self.output_raster_layer = self.parameterAsOutputLayer(
            parameters, OUTPUT_RASTER, context
        )
        self.create_projection_file(output_path_raster=Path(self.output_raster_layer))
        self.set_output_parameter_value(OUTPUT_RASTER, self.output_raster_layer)

        # === SAVE_PROPERTIES

        f_save_properties = self.parameterAsString(parameters, SAVE_PROPERTIES, context)

        self.set_output_parameter_value(SAVE_PROPERTIES, f_save_properties)

    def set_properties_values(self, parameters, context, feedback):
        """set properties values."""

        self.set_properties_input_values(parameters, context, feedback)

        self.set_properties_algorithm_values(parameters, context, feedback)

        self.set_properties_output_values(parameters, context, feedback)

    def get_properties_lines(self) -> list[str]:
        """get properties lines."""
        properties_lines: list[str] = []

        properties_lines.append("treatment=search_and_replace")
        properties_lines.append(
            format_path_for_properties_file(
                f"input_raster={self.input_raster_layer}", isWindows()
            )
        )
        properties_lines.append(
            format_path_for_properties_file(
                f"output_raster={self.output_raster_layer}", isWindows()
            )
        )
        properties_lines.append(f"changes={{{self.changes}}}")
        properties_lines.append(f"nodata_value={self.nodata_value}")
        return properties_lines
