# -*- coding: utf-8 -*-

from pathlib import Path

from qgis.core import (
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
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

from ..chloe_algorithm import ChloeAlgorithm
from ..helpers.constants import (
    DOMAINS,
    INPUT_RASTER,
    OUTPUT_RASTER,
    SAVE_PROPERTIES,
    UTILS_GROUP_ID,
    UTILS_GROUP_NAME,
)


class ClassificationAlgorithm(ChloeAlgorithm):
    """
    Classification algorithm
    """

    def __init__(self):
        super().__init__()

        self.input_raster_layer: str = ""
        self.output_raster_layer: str = ""
        self.domains: str = ""

    def initAlgorithm(self, config=None):
        self.init_input_params()
        self.init_algorithm_params()
        self.init_output_params()

    def init_input_params(self):
        """Init input parameters."""
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
        # DOMAINS
        domains_param = QgsProcessingParameterString(
            name=DOMAINS,
            description=self.tr("New classification"),
            defaultValue="",
        )
        domains_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.classification_table.widget_wrapper.ChloeClassificationTableWidgetWrapper",
                    "input_raster_param_name": INPUT_RASTER,
                    "parent_widget_config": {
                        "linked_parameters": [
                            {
                                "parameter_name": INPUT_RASTER,
                                "action": "check_domains",
                            },
                        ]
                    },
                }
            }
        )
        self.addParameter(domains_param)

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
        return "classification"

    def displayName(self):
        return self.tr("classification")

    def group(self):
        return self.tr(UTILS_GROUP_NAME)

    def groupId(self):
        return UTILS_GROUP_ID

    def commandName(self):
        return "classification"

    def set_properties_input_values(self, parameters, context, feedback):
        """Set input values."""
        self.input_raster_layer = self.parameterRasterAsFilePath(
            parameters, INPUT_RASTER, context
        )

    def set_properties_algorithm_values(self, parameters, context, feedback):
        """Set algorithm parameters."""
        self.domains = self.parameterAsString(parameters, DOMAINS, context)

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""
        self.output_raster_layer = self.parameterAsOutputLayer(
            parameters, OUTPUT_RASTER, context
        )
        self.create_projection_file(output_path_raster=Path(self.output_raster_layer))
        self.set_output_parameter_value(OUTPUT_RASTER, self.output_raster_layer)

        # === SAVE_PROPERTIES

        f_save_properties: str = self.parameterAsString(
            parameters, SAVE_PROPERTIES, context
        )

        self.set_output_parameter_value(SAVE_PROPERTIES, f_save_properties)

    def set_properties_values(self, parameters, context, feedback):
        """set properties values."""

        self.set_properties_input_values(parameters, context, feedback)

        self.set_properties_algorithm_values(parameters, context, feedback)

        self.set_properties_output_values(parameters, context, feedback)

    def get_properties_lines(self) -> list[str]:
        """get properties lines."""
        properties_lines: list[str] = []

        properties_lines.append("treatment=classification")
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
        properties_lines.append(f"domains={{{self.domains}}}")
        return properties_lines
