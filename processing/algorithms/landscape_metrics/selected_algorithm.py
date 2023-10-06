# -*- coding: utf-8 -*-

from typing import Union
from qgis.core import (
    QgsProcessingParameterDefinition,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterFolderDestination,
)

from processing.tools.system import isWindows

from ...gui.custom_widgets.constants import CUSTOM_WIDGET_DIRECTORY


from ..chloe_algorithm import ChloeAlgorithm
from ..helpers.constants import (
    ANALYZE_TYPE,
    DISTANCE_FUNCTION,
    FRICTION_FILE,
    INPUT_RASTER,
    METRICS,
    OUTPUT_CSV,
    OUTPUT_WINDOWS_PATH_DIR,
    PIXEL_POINT_SELECTOR_OPTIONS,
    PIXELS_POINTS_FILE,
    PIXELS_POINTS_SELECT,
    SAVE_PROPERTIES,
    WINDOW_SHAPE,
    WINDOW_SIZES,
)

from ...helpers.helpers import (
    convert_to_odd,
    enum_to_list,
    format_path_for_properties_file,
    get_enum_order_as_int,
)
from ..helpers.enums import AnalyzeType, AnalyzeTypeFastMode, WindowShapeType

# Main dialog


class SelectedAlgorithm(ChloeAlgorithm):
    """Algorithm selection."""

    def __init__(self):
        super().__init__()

        # properties values
        self.input_raster_layer: str = ""
        self.window_sizes: int = 0
        self.metrics: str = ""
        self.window_shape: str = ""
        self.friction_file: str = ""
        self.analyze_type: str = ""
        self.distance_formula: str = ""
        self.pixels_point_selection: Union[int, None] = None
        self.pixels_points_file: str = ""
        self.output_csv: str = ""
        self.output_windows_path_dir: str = ""

    def initAlgorithm(self, config=None):
        self.init_input_params()
        self.init_algorithm_params()
        self.init_algorithm_advanced_params()
        self.init_output_params()

    def init_input_params(self):
        """Init input parameters."""
        input_raster_param = QgsProcessingParameterRasterLayer(
            name=INPUT_RASTER, description=self.tr("Input layer asc")
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
        # METRICS

        metrics_param = QgsProcessingParameterString(
            name=METRICS, description=self.tr("Select metrics")
        )

        metrics_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.double_combobox.widget_wrapper.ChloeDoubleComboboxWidgetWrapper",
                    "default_selected_metric": "diversity metrics",
                    "input_raster_layer_param_name": INPUT_RASTER,
                    "parentWidgetConfig": {
                        "linkedParams": [
                            {
                                "paramName": INPUT_RASTER,
                                "refreshMethod": "refresh_metrics_combobox",
                            },
                        ]
                    },
                }
            }
        )

        self.addParameter(metrics_param)

        # WINDOWS SIZE

        window_size_param = QgsProcessingParameterNumber(
            name=WINDOW_SIZES,
            description=self.tr("Windows sizes (pixels)"),
            defaultValue=3,
            minValue=3,
        )
        self.addParameter(window_size_param)

        # PIXELS POINTS SELECT

        point_pixel_selector_param = QgsProcessingParameterEnum(
            name=PIXELS_POINTS_SELECT,
            description=self.tr("Pixels/points selection"),
            options=PIXEL_POINT_SELECTOR_OPTIONS,
        )

        self.addParameter(point_pixel_selector_param)

        # PIXELS_POINTS FILE
        self.addParameter(
            QgsProcessingParameterFile(
                name=PIXELS_POINTS_FILE,
                description=self.tr("Pixels/points file"),
                optional=False,
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
                            "enabled_by_value": get_enum_order_as_int(
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
        friction_file_param = QgsProcessingParameterFile(
            name=FRICTION_FILE, description=self.tr("Friction file"), optional=True
        )
        friction_file_param.setFileFilter("GeoTIFF (*.tif *.TIF);; ASCII (*.asc *.ASC)")
        friction_file_param.setFlags(
            friction_file_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
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
                            "enabled_by_value": get_enum_order_as_int(
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

        csv_output_parameter = QgsProcessingParameterFileDestination(
            name=OUTPUT_CSV,
            description=self.tr("Output csv"),
            fileFilter="CSV (*.csv *.CSV)",
            createByDefault=False,
        )

        self.addParameter(csv_output_parameter)

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
        return "selected"

    def displayName(self):
        return self.tr("selected")

    def group(self):
        return self.tr("landscape metrics")

    def groupId(self):
        return "landscapemetrics"

    def commandName(self):
        return "selected"

    def set_properties_input_values(self, parameters, context):
        """Set input values."""

        self.input_raster_layer = self.parameterRasterAsFilePath(
            parameters, INPUT_RASTER, context
        )

    def set_properties_algorithm_values(self, parameters, context):
        """Set algorithm parameters."""
        self.window_shape = enum_to_list(WindowShapeType)[
            self.parameterAsEnum(parameters, WINDOW_SHAPE, context)
        ]

        self.friction_file = self.parameterAsString(parameters, FRICTION_FILE, context)

        self.window_sizes = self.parameterAsInt(parameters, WINDOW_SIZES, context)

        self.analyze_type = enum_to_list(AnalyzeType)[
            self.parameterAsEnum(parameters, ANALYZE_TYPE, context)
        ]

        self.distance_formula = self.parameterAsString(
            parameters, DISTANCE_FUNCTION, context
        )

        self.pixels_point_selection = self.parameterAsInt(
            parameters, PIXELS_POINTS_SELECT, context
        )

        self.pixels_points_file = self.parameterAsString(
            parameters, PIXELS_POINTS_FILE, context
        )

        self.metrics = self.parameterAsString(parameters, METRICS, context)

    def set_properties_output_values(self, parameters, context):
        """Set output values."""
        self.output_csv = self.parameterAsString(parameters, OUTPUT_CSV, context)

        self.output_windows_path_dir = self.parameterAsString(
            parameters, OUTPUT_WINDOWS_PATH_DIR, context
        )
        self.set_output_parameter_value(OUTPUT_CSV, self.output_csv)
        if self.output_windows_path_dir:
            self.set_output_parameter_value(
                OUTPUT_WINDOWS_PATH_DIR, self.output_windows_path_dir
            )

        f_save_properties = self.parameterAsString(parameters, SAVE_PROPERTIES, context)
        self.set_output_parameter_value(SAVE_PROPERTIES, f_save_properties)

    def set_properties_values(self, parameters, context):
        """set properties values."""

        self.set_properties_input_values(parameters, context)

        self.set_properties_algorithm_values(parameters, context)

        self.set_properties_output_values(parameters, context)

    def get_properties_lines(self) -> list[str]:
        """get properties lines."""

        properties_lines: list[str] = []

        properties_lines.append(f"treatment={self.name()}")
        properties_lines.append(
            format_path_for_properties_file(
                f"input_raster={self.input_raster_layer}", isWindows()
            )
        )

        properties_lines.append(
            f"sizes={{{str(convert_to_odd(input_integer=self.window_sizes))}}}"
        )

        properties_lines.append(f"metrics={{{self.metrics}}}")

        properties_lines.append(f"distance_type={str(self.analyze_type)}")
        if self.analyze_type == AnalyzeType.WEIGHTED.value:
            properties_lines.append(f"distance_function={str(self.distance_formula)}")
        properties_lines.append(f"shape={str(self.window_shape)}")
        if self.window_shape == WindowShapeType.FUNCTIONAL.value:
            properties_lines.append(f"friction={self.friction_file}")

        pixels_points_files = format_path_for_properties_file(
            self.pixels_points_file, isWindows()
        )

        if self.pixels_point_selection == 0:  # pixel(s) file
            properties_lines.append(f"pixels={pixels_points_files}")
        elif self.pixels_point_selection == 1:  # point(s) file
            properties_lines.append(f"points={pixels_points_files}")

        properties_lines.append(
            format_path_for_properties_file(
                f"output_csv={self.output_csv}", isWindows()
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
