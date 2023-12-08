from typing import Union
from qgis.core import (
    QgsProcessingParameterDefinition,
    QgsMapLayer,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterFolderDestination,
)

from processing.tools.system import isWindows

from ...gui.custom_widgets.constants import CUSTOM_WIDGET_DIRECTORY

from ...gui.custom_parameters.chloe_raster_parameter_file_input import (
    ChloeRasterParameterFileInput,
)
from ...helpers.helpers import (
    enum_to_list,
    format_path_for_properties_file,
    get_enum_element_index,
)
from ..chloe_algorithm import ChloeAlgorithm
from ..helpers.constants import (
    ANALYZE_TYPE,
    DISTANCE_FUNCTION,
    FRICTION_FILE,
    INPUT_RASTER,
    LANDSCAPE_METRICS_GROUP_ID,
    LANDSCAPE_METRICS_GROUP_NAME,
    LANDSCAPE_METRICS_MULTI_GROUP_ID,
    LANDSCAPE_METRICS_MULTI_GROUP_NAME,
    METRICS,
    OUTPUT_CSV,
    OUTPUT_DIR,
    OUTPUT_WINDOWS_PATH_DIR,
    POINTS_FILE,
    SAVE_PROPERTIES,
    WINDOW_SHAPE,
    WINDOW_SIZES,
)


from ..helpers.enums import AnalyzeType, AnalyzeTypeFastMode, WindowShapeType

# Main dialog


class SelectedMultiAlgorithm(ChloeAlgorithm):
    """Algorithm selected multi."""

    def __init__(self):
        super().__init__()

        # properties values
        self.input_raster_layer: str = ""
        self.window_sizes: str = ""
        self.metrics: str = ""
        self.window_shape: str = ""
        self.friction_file: str = ""
        self.analyze_type: str = ""
        self.distance_formula: str = ""
        self.points_file: str = ""
        self.output_folder: str = ""
        self.output_windows_path_dir: str = ""

    def initAlgorithm(self, config=None):
        self.init_input_params()
        self.init_algorithm_params()
        self.init_algorithm_advanced_params()
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
        # METRICS

        metrics_param = QgsProcessingParameterString(
            name=METRICS, description=self.tr("Select metrics")
        )

        metrics_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.double_list_selector.widget_wrapper.ChloeDoubleListSelectorWidgetWrapper",
                    "default_selected_metric": "diversity metrics",
                    "input_raster_layer_param_name": INPUT_RASTER,
                    "parent_widget_config": {
                        "linked_parameters": [
                            {
                                "parameter_name": INPUT_RASTER,
                                "action": "refresh_metrics_combobox",
                            },
                        ]
                    },
                }
            }
        )

        self.addParameter(metrics_param)

        # WINDOWS SIZE

        window_size_param = QgsProcessingParameterString(
            name=WINDOW_SIZES, description=self.tr("Windows sizes (pixels)")
        )

        window_size_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.number_list_selector.widget_wrapper.ChloeIntListSelectorWidgetWrapper",
                    "default_value": 3,
                    "max_value": 100001,
                    "min_value": 3,
                    "single_step_value": 2,
                }
            }
        )
        self.addParameter(window_size_param)

        # PIXELS_POINTS FILE
        self.addParameter(
            QgsProcessingParameterFile(
                name=POINTS_FILE,
                description=self.tr("Point file"),
                optional=False,
                fileFilter="CSV (*.csv *.CSV);;TXT (*.txt *.TXT);; DBF (*.dbf *.DBF)",
            )
        )

    def init_algorithm_advanced_params(self):
        """ "Init algorithm advanced parameters."""
        # WINDOWS SHAPE

        window_shape_param = QgsProcessingParameterEnum(
            name=WINDOW_SHAPE,
            description=self.tr("Window shape"),
            options=enum_to_list(WindowShapeType),
        )

        window_shape_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.enum_update_state.widget_wrapper.ChloeEnumUpdateStateWidgetWrapper",
                    "enabled_widgets_configs": [
                        {
                            "param_name": FRICTION_FILE,
                            "enabled_by_value": get_enum_element_index(
                                WindowShapeType.FUNCTIONAL
                            ),
                        }
                    ],
                }
            }
        )
        window_shape_param.setFlags(
            window_shape_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(window_shape_param)

        # FRICTION FILE
        friction_file_param = ChloeRasterParameterFileInput(
            name=FRICTION_FILE,
            description=self.tr("Friction file"),
            optional=True,
        )
        friction_file_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.layer_input.widget_wrapper.ChloeRasterInputWidgetWrapper"
                }
            }
        )

        friction_file_param.setFlags(
            friction_file_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(friction_file_param)
        # ANALYZE TYPE

        analyze_type_param = QgsProcessingParameterEnum(
            name=ANALYZE_TYPE,
            description=self.tr("Analyze type"),
            options=enum_to_list(AnalyzeType),
        )

        analyze_type_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.enum_update_state.widget_wrapper.ChloeEnumUpdateStateWidgetWrapper",
                    "fast_mode_options": enum_to_list(AnalyzeTypeFastMode),
                    "enabled_widgets_configs": [
                        {
                            "param_name": DISTANCE_FUNCTION,
                            "enabled_by_value": get_enum_element_index(
                                AnalyzeType.WEIGHTED
                            ),
                        }
                    ],
                }
            }
        )

        analyze_type_param.setFlags(
            analyze_type_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(analyze_type_param)

        # DISTANCE FUNCTION

        distance_function_param = QgsProcessingParameterString(
            name=DISTANCE_FUNCTION,
            description=self.tr("Distance function"),
            defaultValue="exp(-pow(distance, 2)/pow(dmax/2, 2))",
            optional=True,
        )
        distance_function_param.setFlags(
            distance_function_param.flags()
            | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(distance_function_param)

    def init_output_params(self):
        """Init output parameters."""
        # === OUTPUT PARAMETERS ===

        output_folder_parameter = QgsProcessingParameterFolderDestination(
            name=OUTPUT_DIR,
            description=self.tr("Output folder"),
        )
        self.addParameter(output_folder_parameter)

        windows_raster_folder_param = QgsProcessingParameterFolderDestination(
            name=OUTPUT_WINDOWS_PATH_DIR,
            description=self.tr("Output windows folder"),
            optional=True,
            createByDefault=False,
        )

        self.addParameter(windows_raster_folder_param)

        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=SAVE_PROPERTIES,
                description=self.tr("Properties file"),
                fileFilter="Properties (*.properties)",
            )
        )

    def name(self):
        return "selected multi"

    def displayName(self):
        return self.tr("selected multi")

    def group(self):
        return self.tr(LANDSCAPE_METRICS_MULTI_GROUP_NAME)

    def groupId(self):
        return LANDSCAPE_METRICS_MULTI_GROUP_ID

    def commandName(self):
        return "selected multi"

    def set_properties_input_values(self, parameters, context, feedback):
        """Set input values."""

        self.input_raster_layer = self.parameterAsLayer(
            parameters, INPUT_RASTER, context
        ).source()

    def set_properties_algorithm_values(self, parameters, context, feedback):
        """Set algorithm parameters."""
        self.window_shape = enum_to_list(WindowShapeType)[
            self.parameterAsEnum(parameters, WINDOW_SHAPE, context)
        ]

        friction_layer: Union[QgsMapLayer, None] = self.parameterAsLayer(
            parameters, FRICTION_FILE, context
        )
        self.friction_file = (
            friction_layer.source()
            if friction_layer is not None
            and self.window_shape == WindowShapeType.FUNCTIONAL.value
            else ""
        )

        self.window_sizes = self.parameterAsString(parameters, WINDOW_SIZES, context)

        self.analyze_type = enum_to_list(AnalyzeType)[
            self.parameterAsEnum(parameters, ANALYZE_TYPE, context)
        ]

        self.distance_formula = self.parameterAsString(
            parameters, DISTANCE_FUNCTION, context
        )

        self.points_file = self.parameterAsString(parameters, POINTS_FILE, context)

        self.metrics = self.parameterAsString(parameters, METRICS, context)

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""
        self.output_folder = self.parameterAsString(parameters, OUTPUT_DIR, context)
        self.set_output_parameter_value(OUTPUT_DIR, self.output_folder)

        self.output_windows_path_dir = self.parameterAsString(
            parameters, OUTPUT_WINDOWS_PATH_DIR, context
        )

        if self.output_windows_path_dir:
            self.set_output_parameter_value(
                OUTPUT_WINDOWS_PATH_DIR, self.output_windows_path_dir
            )

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

        properties_lines.append("treatment=selected")
        properties_lines.append(
            format_path_for_properties_file(
                f"input_raster={self.input_raster_layer}", isWindows()
            )
        )

        properties_lines.append(f"sizes={{{self.window_sizes}}}")

        properties_lines.append(f"metrics={{{self.metrics}}}")

        properties_lines.append(f"distance_type={str(self.analyze_type)}")
        if self.analyze_type == AnalyzeType.WEIGHTED.value:
            properties_lines.append(f"distance_function={str(self.distance_formula)}")
        properties_lines.append(f"shape={str(self.window_shape)}")
        if self.friction_file:
            properties_lines.append(f"friction={self.friction_file}")

        points_files = format_path_for_properties_file(self.points_file, isWindows())

        properties_lines.append(f"points={points_files}")

        properties_lines.append(
            format_path_for_properties_file(
                f"output_folder={self.output_folder}", isWindows()
            )
        )

        if self.output_windows_path_dir:
            properties_lines.append(
                format_path_for_properties_file(
                    f"windows_path={self.output_windows_path_dir}\\",
                    isWindows(),
                )
            )

        return properties_lines
