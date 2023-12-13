from typing import Union
from qgis.core import (
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsMapLayer,
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
    CLUSTER,
    CLUSTER_DISTANCE,
    CLUSTER_DISTANCE_FILE,
    CLUSTER_TYPE,
    INPUT_RASTER,
    OUTPUT_RASTER,
    OUTPUT_CSV,
    SAVE_PROPERTIES,
    UTILS_GROUP_ID,
    UTILS_GROUP_NAME,
)

from ..helpers.enums import ClusterType


class ClusterAlgorithm(ChloeAlgorithm):
    """
    Cluster Algorithm
    """

    def __init__(self):
        super().__init__()

        self.input_raster: str = ""
        self.cluster_values: str = ""
        self.cluster_type: str = ""
        self.cluster_distance: str = ""
        self.distance_file: str = ""
        self.output_csv: str = ""
        self.output_raster: str = ""

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

        cluster_parameter = QgsProcessingParameterString(
            name=CLUSTER,
            description=self.tr("Clusters from value(s)"),
            defaultValue="",
        )
        cluster_parameter.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.values_selector.widget_wrapper.ChloeRasterValuesWidgetWrapper"
                }
            }
        )

        self.addParameter(cluster_parameter)

        cluster_type_parameter = QgsProcessingParameterEnum(
            name=CLUSTER_TYPE,
            description=self.tr("Cluster type"),
            options=enum_to_list(ClusterType),
        )

        cluster_type_parameter.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.enum_update_state.widget_wrapper.ChloeEnumUpdateStateWidgetWrapper",
                    "enabled_widgets_configs": [
                        {
                            "param_name": CLUSTER_DISTANCE,
                            "enabled_by_value": get_enum_element_index(
                                ClusterType.DISTANCE
                            ),
                        },
                        {
                            "param_name": CLUSTER_DISTANCE_FILE,
                            "enabled_by_value": get_enum_element_index(
                                ClusterType.DISTANCE
                            ),
                        },
                    ],
                }
            }
        )

        self.addParameter(cluster_type_parameter)

        # CLUSTER DISTANCE
        self.addParameter(
            QgsProcessingParameterNumber(
                name=CLUSTER_DISTANCE,
                description=self.tr("Distance in meters (only for distance)"),
                type=QgsProcessingParameterNumber.Double,
                optional=True,
                minValue=0,
            )
        )

        distance_file_param = ChloeRasterParameterFileInput(
            name=CLUSTER_DISTANCE_FILE,
            description=self.tr("Distance file"),
            optional=True,
        )

        distance_file_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.layer_input.widget_wrapper.ChloeRasterInputWidgetWrapper"
                }
            }
        )
        self.addParameter(distance_file_param)

        # CLUSTER MIN AREA
        # TODO : remove ?
        # self.addParameter(
        #     QgsProcessingParameterNumber(
        #         name=self.CLUSTER_MIN_AREA,
        #         description=self.tr("Minimal area (Ha)"),
        #         type=QgsProcessingParameterNumber.Double,
        #         defaultValue=0.0,
        #         minValue=0.0,
        #     )
        # )

    def init_output_params(self):
        """Init output parameters."""
        csv_output_parameter = QgsProcessingParameterFileDestination(
            name=OUTPUT_CSV,
            description=self.tr("Output csv"),
            fileFilter="CSV (*.csv *.CSV)",
            optional=True,
            createByDefault=False,
        )
        self.addParameter(csv_output_parameter)

        raster_output_parameter = ChloeRasterParameterFileDestination(
            name=OUTPUT_RASTER,
            description=self.tr("Output Raster"),
            optional=True,
            createByDefault=False,
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
        return "cluster"

    def displayName(self):
        return self.tr("Clustering")

    def group(self):
        return self.tr(UTILS_GROUP_NAME)

    def groupId(self):
        return UTILS_GROUP_ID

    def commandName(self):
        return "cluster"

    def checkParameterValues(self, parameters, context):
        """Override checkParameterValues base class method. check additional parameters."""

        output_csv = self.parameterAsOutputLayer(parameters, OUTPUT_CSV, context)
        output_raster = self.parameterAsOutputLayer(parameters, OUTPUT_RASTER, context)

        if not output_csv and not output_raster:
            return False, self.tr("You must select at least one output file")

        # If these parameters are valid, call the parent class's checkParameterValues method for the rest
        return super().checkParameterValues(parameters, context)

    def set_properties_input_values(self, parameters, context, feedback):
        """Set input values."""
        self.input_raster = self.parameterAsLayer(
            parameters, INPUT_RASTER, context
        ).source()

    def set_properties_algorithm_values(self, parameters, context, feedback):
        """Set algorithm parameters."""

        self.cluster_values = self.parameterAsString(parameters, CLUSTER, context)

        self.cluster_type = str(
            enum_to_list(enum_class=ClusterType, return_enum_names=True)[
                self.parameterAsEnum(parameters, CLUSTER_TYPE, context)
            ]
        )

        self.cluster_distance = (
            self.parameterAsString(parameters, CLUSTER_DISTANCE, context)
            if self.cluster_type == ClusterType.DISTANCE.name
            else ""
        )

        distance_layer: Union[QgsMapLayer, None] = self.parameterAsLayer(
            parameters, CLUSTER_DISTANCE_FILE, context
        )
        self.distance_file = (
            distance_layer.source()
            if distance_layer is not None
            and self.cluster_type == ClusterType.DISTANCE.name
            else ""
        )

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""
        self.output_csv = self.parameterAsString(parameters, OUTPUT_CSV, context)
        self.set_output_parameter_value(OUTPUT_CSV, self.output_csv)

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

        properties_lines.append("treatment=cluster")
        properties_lines.append(
            format_path_for_properties_file(
                input_string=f"input_raster={self.input_raster}",
                is_windows_system=isWindows(),
            )
        )

        if self.output_csv:
            properties_lines.append(
                format_path_for_properties_file(
                    input_string=f"output_csv={self.output_csv}",
                    is_windows_system=isWindows(),
                )
            )

        if self.output_raster:
            properties_lines.append(
                format_path_for_properties_file(
                    input_string=f"output_raster={self.output_raster}",
                    is_windows_system=isWindows(),
                )
            )

        properties_lines.append(f"cluster_sources={{{self.cluster_values}}}")
        properties_lines.append(f"cluster_type={self.cluster_type}")
        if self.distance_file:
            properties_lines.append(
                format_path_for_properties_file(
                    input_string=f"distance_raster={self.distance_file}",
                    is_windows_system=isWindows(),
                )
            )

        if self.cluster_distance:
            properties_lines.append(f"max_distance={str(self.cluster_distance)}")
        return properties_lines
