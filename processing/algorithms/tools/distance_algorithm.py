from typing import Union
from qgis.core import (
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsMapLayer,
    QgsProcessingException,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows

from ...gui.custom_parameters.chloe_raster_parameter_file_destination import (
    ChloeRasterParameterFileDestination,
)
from ...gui.custom_parameters.chloe_raster_parameter_file_input import (
    ChloeRasterParameterFileInput,
)
from ...gui.custom_widgets.constants import CUSTOM_WIDGET_DIRECTORY

from ...helpers.helpers import (
    enum_to_list,
    format_path_for_properties_file,
    get_enum_element_index,
)

from ..chloe_algorithm import ChloeAlgorithm
from ..helpers.constants import (
    DISTANCE_MAX,
    DISTANCE_TYPE,
    DISTANCE_VALUES,
    FRICTION_FILE,
    INPUT_RASTER,
    OUTPUT_RASTER,
    SAVE_PROPERTIES,
    UTILS_GROUP_ID,
    UTILS_GROUP_NAME,
)

from ..helpers.enums import DistanceType


class DistanceAlgorithm(ChloeAlgorithm):
    """
    Distance Algorithm
    """

    def __init__(self):
        super().__init__()

        self.input_raster: str = ""
        self.values: str = ""
        self.distance_type: str = ""
        self.friction_file: str = ""
        self.distance_max: float = 0.0
        self.output_raster: str = ""

    def initAlgorithm(self, config=None):
        self.init_input_params()
        self.init_algorithm_params()
        self.init_output_params()

    def init_input_params(self):
        """Init input parameters."""
        input_asc_param = ChloeRasterParameterFileInput(
            name=INPUT_RASTER, description=self.tr("Input raster layer")
        )

        input_asc_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.layer_input.widget_wrapper.ChloeRasterInputWidgetWrapper"
                }
            }
        )
        self.addParameter(input_asc_param)

    def init_algorithm_params(self):
        """Init algorithm parameters."""

        values_param = QgsProcessingParameterString(
            name=DISTANCE_VALUES,
            description=self.tr("Values"),
            defaultValue="",
        )
        values_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.values_selector.widget_wrapper.ChloeRasterValuesWidgetWrapper"
                }
            }
        )

        self.addParameter(values_param)

        distance_type_parameter = QgsProcessingParameterEnum(
            name=DISTANCE_TYPE,
            description=self.tr("Distance type"),
            options=enum_to_list(DistanceType),
        )

        distance_type_parameter.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.enum_update_state.widget_wrapper.ChloeEnumUpdateStateWidgetWrapper",
                    "enabled_widgets_configs": [
                        {
                            "param_name": FRICTION_FILE,
                            "enabled_by_value": get_enum_element_index(
                                DistanceType.FUNCTIONAL
                            ),
                        },
                    ],
                }
            }
        )

        self.addParameter(distance_type_parameter)

        distance_friction_param = ChloeRasterParameterFileInput(
            name=FRICTION_FILE,
            description=self.tr("Friction file"),
            optional=True,
        )

        distance_friction_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.layer_input.widget_wrapper.ChloeRasterInputWidgetWrapper"
                }
            }
        )
        self.addParameter(distance_friction_param)

        self.addParameter(
            QgsProcessingParameterNumber(
                name=DISTANCE_MAX,
                description=self.tr("Maximum distance (in meters)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=None,
                minValue=1,
                optional=True,
            )
        )

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
        return "distance"

    def displayName(self):
        return self.tr("Distance")

    def group(self):
        return self.tr(UTILS_GROUP_NAME)

    def groupId(self):
        return UTILS_GROUP_ID

    def commandName(self):
        return "distance"

    def set_properties_input_values(self, parameters, context, feedback):
        """Set input values."""

        self.input_raster = self.parameterAsLayer(
            parameters, INPUT_RASTER, context
        ).source()

    def set_properties_algorithm_values(self, parameters, context, feedback):
        """Set algorithm parameters."""

        self.values = self.parameterAsString(parameters, DISTANCE_VALUES, context)

        self.distance_type = str(
            enum_to_list(enum_class=DistanceType, return_enum_names=True)[
                self.parameterAsEnum(parameters, DISTANCE_TYPE, context)
            ]
        )

        friction_layer: Union[QgsMapLayer, None] = self.parameterAsLayer(
            parameters, FRICTION_FILE, context
        )
        self.friction_file = (
            friction_layer.source()
            if friction_layer is not None
            and self.distance_type == DistanceType.FUNCTIONAL.name
            else ""
        )

        self.distance_max = self.parameterAsDouble(parameters, DISTANCE_MAX, context)

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""

        self.output_raster = self.parameterAsOutputLayer(
            parameters, OUTPUT_RASTER, context
        )

        self.set_output_parameter_value(OUTPUT_RASTER, self.output_raster)

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

        properties_lines.append("treatment=distance")
        properties_lines.append(
            format_path_for_properties_file(
                input_string=f"input_raster={self.input_raster}",
                is_windows_system=isWindows(),
            )
        )

        properties_lines.append(f"distance_sources={{{self.values}}}")
        properties_lines.append(f"distance_type={self.distance_type}")
        if self.friction_file:
            properties_lines.append(
                format_path_for_properties_file(
                    input_string=f"friction_raster={self.friction_file}",
                    is_windows_system=isWindows(),
                )
            )

        if self.distance_max >= 1:
            properties_lines.append(f"max_distance={str(self.distance_max)}")

        properties_lines.append(
            format_path_for_properties_file(
                input_string=f"output_raster={self.output_raster}",
                is_windows_system=isWindows(),
            )
        )
        return properties_lines
