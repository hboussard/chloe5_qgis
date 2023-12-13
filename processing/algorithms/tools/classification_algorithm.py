from qgis.core import (
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
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.layer_input.widget_wrapper.ChloeRasterInputWidgetWrapper"
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
        return self.tr("Classification")

    def group(self):
        return self.tr(UTILS_GROUP_NAME)

    def groupId(self):
        return UTILS_GROUP_ID

    def commandName(self):
        return "classification"

    def set_properties_input_values(self, parameters, context, feedback):
        """Set input values."""
        self.input_raster_layer = self.parameterAsLayer(
            parameters, INPUT_RASTER, context
        ).source()

    def set_properties_algorithm_values(self, parameters, context, feedback):
        """Set algorithm parameters.
        domains widget returns a list containing a list of domains and a string containing the domains to be used in the properties file.
        first value of this list is the propertie string and the second is the list of domains  .
        This allows the use of the custom classification domain in modeler mode to be saved in the model xml file.
        """

        domains_param_value: "list[list[str] | str]" = self.parameterAsMatrix(
            parameters, DOMAINS, context
        )
        self.domains = domains_param_value[0]

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""
        self.output_raster_layer = self.parameterAsOutputLayer(
            parameters, OUTPUT_RASTER, context
        )

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
