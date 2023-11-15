# -*- coding: utf-8 -*-

from enum import Enum
from pathlib import Path
from qgis.core import (
    QgsProcessingParameterDefinition,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows

from ....helpers.helpers import convert_int_to_odd
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
    ANALYZE_TYPE,
    DELTA_DISPLACEMENT,
    DISTANCE_FUNCTION,
    FAST,
    FILTER_ANALYZE,
    FILTER_NO_ANALYZE,
    FRICTION_FILE,
    INPUT_RASTER,
    INTERPOLATE_VALUES_BOOL,
    LANDSCAPE_METRICS_GROUP_ID,
    LANDSCAPE_METRICS_GROUP_NAME,
    MAXIMUM_RATE_MISSING_VALUES,
    METRICS,
    OUTPUT_RASTER,
    OUTPUT_CSV,
    SAVE_PROPERTIES,
    WINDOW_SHAPE,
    WINDOW_SIZES,
)
from ..helpers.enums import AnalyzeType, AnalyzeTypeFastMode, WindowShapeType


class SlidingAlgorithm(ChloeAlgorithm):
    """Algorithm sliding."""

    def __init__(self):
        super().__init__()

        # properties values
        self.input_raster: str = ""
        self.is_fast_mode: bool = False
        self.window_shape: str = ""
        self.friction_file: str = ""
        self.window_sizes: int = 0
        self.analyze_type: str = ""
        self.distance_formula: str = ""
        self.delta_displacement: int = 0
        self.b_interpolate_values: bool = False
        self.filter_analyze: str = ""
        self.filter_no_analyze: str = ""
        self.maximum_rate_missing_values: int = 0
        self.metrics: str = ""
        self.output_csv: str = ""
        self.output_raster: str = ""

    def initAlgorithm(self, config=None):
        self.init_input_params()
        self.init_algorithm_params()
        self.init_algorithm_advanced_params()
        self.init_output_params()

    def init_input_params(self):
        """Init input parameters."""
        # INPUT ASC
        input_asc_param = ChloeRasterParameterFileInput(
            name=INPUT_RASTER, description=self.tr("Input raster layer")
        )

        input_asc_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.raster_input.widget_wrapper.ChloeAscRasterWidgetWrapper"
                }
            }
        )
        self.addParameter(input_asc_param)

    def init_algorithm_params(self):
        """Init algorithm parameters."""
        # algorithm is fast
        fast_mode_param: QgsProcessingParameterBoolean = QgsProcessingParameterBoolean(
            name=FAST, description=self.tr("Fast mode"), defaultValue=False
        )
        fast_mode_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.checkbox_update_state.widget_wrapper.ChloeCheckboxUpdateStateWidgetWrapper",
                    "enabled_widgets_configs": [
                        {"param_name": WINDOW_SHAPE, "enabled_by_value": False},
                        {"param_name": DISTANCE_FUNCTION, "enabled_by_value": False},
                        {"param_name": FRICTION_FILE, "enabled_by_value": False},
                    ],
                }
            }
        )

        self.addParameter(fast_mode_param)
        # METRICS

        metrics_param: QgsProcessingParameterString = QgsProcessingParameterString(
            name=METRICS, description=self.tr("Select metrics")
        )

        metrics_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.double_combobox.widget_wrapper.ChloeDoubleComboboxWidgetWrapper",
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

        # WINDOW SIZE
        window_size_parameter = QgsProcessingParameterNumber(
            name=WINDOW_SIZES,
            description=self.tr("Windows sizes (pixels)"),
            defaultValue=3,
            minValue=3,
        )

        window_size_parameter.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.int_spin_box.widget_wrapper.ChloeOddEvenIntSpinboxWrapper",
                    "initial_value": 3,
                    "min_value": 3,
                    "max_value": 100001,
                    "odd_mode": True,
                }
            }
        )

        self.addParameter(window_size_parameter)

    def init_algorithm_advanced_params(self):
        """Init algorithm advanced parameters."""
        # WINDOW SHAPE

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

        # FRICTION FILE (OPTIONAL)

        friction_file_param = QgsProcessingParameterFile(
            name=FRICTION_FILE, description=self.tr("Friction file"), optional=True
        )
        friction_file_param.setFileFilter("GeoTIFF (*.tif *.TIF);; ASCII (*.asc *.ASC)")
        friction_file_param.setFlags(
            friction_file_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )

        self.addParameter(friction_file_param)

        # ANALYZE TYPE

        analyze_type_param = QgsProcessingParameterEnum(
            name=ANALYZE_TYPE,
            description=self.tr("Prise en compte des distances"),
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
                            "disabled_by_fast_mode": True,
                        },
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

        # DELTA DISPLACEMENT
        delta_displacement_param = QgsProcessingParameterNumber(
            name=DELTA_DISPLACEMENT,
            description=self.tr("Delta displacement (pixels)"),
            defaultValue=1,
            minValue=1,
        )
        delta_displacement_param.setFlags(
            delta_displacement_param.flags()
            | QgsProcessingParameterDefinition.FlagAdvanced
        )

        self.addParameter(delta_displacement_param)

        # INTERPOLATE VALUES BOOL
        interpolate_values_parameter = QgsProcessingParameterBoolean(
            name=INTERPOLATE_VALUES_BOOL,
            description=self.tr("Interpolate Values"),
            defaultValue=False,
        )
        interpolate_values_parameter.setFlags(
            interpolate_values_parameter.flags()
            | QgsProcessingParameterDefinition.FlagAdvanced
        )

        self.addParameter(interpolate_values_parameter)

        # FILTER
        filter_do_analyze_parameter = QgsProcessingParameterString(
            name=FILTER_ANALYZE,
            description=self.tr("Filters - Analyse only"),
            defaultValue="",
            optional=True,
        )
        filter_do_analyze_parameter.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.values_selector.widget_wrapper.ChloeRasterValuesWidgetWrapper"
                }
            }
        )
        filter_do_analyze_parameter.setFlags(
            filter_do_analyze_parameter.flags()
            | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(filter_do_analyze_parameter)

        # UNFILTER
        filter_no_analyze_parameter = QgsProcessingParameterString(
            name=FILTER_NO_ANALYZE,
            description=self.tr("Filters - Do not analyse"),
            defaultValue="",
            optional=True,
        )
        filter_no_analyze_parameter.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.values_selector.widget_wrapper.ChloeRasterValuesWidgetWrapper"
                }
            }
        )

        filter_no_analyze_parameter.setFlags(
            filter_no_analyze_parameter.flags()
            | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(filter_no_analyze_parameter)

        # MAX RATE MISSING VALUES
        max_rate_missing_values_parameteer = QgsProcessingParameterNumber(
            name=MAXIMUM_RATE_MISSING_VALUES,
            description=self.tr("Maximum rate of missing values"),
            minValue=0,
            maxValue=100,
            defaultValue=100,
        )
        max_rate_missing_values_parameteer.setFlags(
            max_rate_missing_values_parameteer.flags()
            | QgsProcessingParameterDefinition.FlagAdvanced
        )

        self.addParameter(max_rate_missing_values_parameteer)

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
        return "sliding"

    def displayName(self):
        return self.tr("sliding")

    def group(self):
        return self.tr(LANDSCAPE_METRICS_GROUP_NAME)

    def groupId(self):
        return LANDSCAPE_METRICS_GROUP_ID

    def commandName(self):
        return "java"

    def checkParameterValues(self, parameters, context):
        """Override checkParameterValues base class method. check additional parameters."""

        input_raster = self.parameterAsString(parameters, INPUT_RASTER, context)

        if not input_raster:
            return False, self.tr("You must select an input raster file")

        output_csv = self.parameterAsOutputLayer(parameters, OUTPUT_CSV, context)
        output_raster = self.parameterAsOutputLayer(parameters, OUTPUT_RASTER, context)

        if not output_csv and not output_raster:
            return False, self.tr("You must select at least one output file")

        # If these parameters are valid, call the parent class's checkParameterValues method for the rest
        return super().checkParameterValues(parameters, context)

    def set_properties_input_values(self, parameters, context, feedback):
        """Set input values."""
        self.input_raster = self.parameterRasterAsFilePath(
            parameters, INPUT_RASTER, context
        )

    def set_properties_algorithm_values(self, parameters, context, feedback):
        """Set algorithm parameters."""

        self.is_fast_mode = self.parameterAsBool(parameters, FAST, context)

        self.window_shape = enum_to_list(WindowShapeType)[
            self.parameterAsEnum(parameters, WINDOW_SHAPE, context)
        ]

        self.friction_file = self.parameterAsString(parameters, FRICTION_FILE, context)

        self.window_sizes = self.parameterAsInt(parameters, WINDOW_SIZES, context)

        analyze_enum_class: Enum = AnalyzeType
        if self.is_fast_mode:
            analyze_enum_class = AnalyzeTypeFastMode

        self.analyze_type = enum_to_list(
            enum_class=analyze_enum_class, return_enum_names=True
        )[self.parameterAsEnum(parameters, ANALYZE_TYPE, context)]

        self.distance_formula = self.parameterAsString(
            parameters, DISTANCE_FUNCTION, context
        )

        self.delta_displacement = self.parameterAsInt(
            parameters, DELTA_DISPLACEMENT, context
        )

        self.b_interpolate_values = self.parameterAsBool(
            parameters, INTERPOLATE_VALUES_BOOL, context
        )

        self.filter_analyze = self.parameterAsString(
            parameters, FILTER_ANALYZE, context
        )
        self.filter_no_analyze = self.parameterAsString(
            parameters, FILTER_NO_ANALYZE, context
        )

        self.maximum_rate_missing_values = self.parameterAsInt(
            parameters, MAXIMUM_RATE_MISSING_VALUES, context
        )
        self.metrics = self.parameterAsString(parameters, METRICS, context)

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""
        self.output_csv = self.parameterAsString(parameters, OUTPUT_CSV, context)
        self.set_output_parameter_value(OUTPUT_CSV, self.output_csv)

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

        self.set_properties_input_values(parameters, context, feedback)

        self.set_properties_algorithm_values(parameters, context, feedback)

        self.set_properties_output_values(parameters, context, feedback)

    def get_properties_lines(self) -> list[str]:
        """get properties lines."""
        properties_lines: list[str] = []

        properties_lines.append("treatment=sliding")
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

        properties_lines.append(
            f"sizes={{{str(convert_int_to_odd(input_integer=self.window_sizes))}}}"
        )
        properties_lines.append(
            f"maximum_nodata_value_rate={str(self.maximum_rate_missing_values)}"
        )

        properties_lines.append(f"distance_type={str(self.analyze_type)}")

        if self.analyze_type == AnalyzeType.WEIGHTED.value:
            properties_lines.append(f"distance_function={str(self.distance_formula)}")

        properties_lines.append(f"metrics={{{self.metrics}}}")
        properties_lines.append(f"delta_displacement={str(self.delta_displacement)}")

        if not self.is_fast_mode:
            properties_lines.append(f"shape={str(self.window_shape)}")

        if (
            self.window_shape == WindowShapeType.FUNCTIONAL.value
            and self.friction_file
            and not self.is_fast_mode
        ):
            properties_lines.append(f"friction={self.friction_file}")

        if self.b_interpolate_values:
            properties_lines.append("interpolation=true")
        elif self.delta_displacement != 1:
            properties_lines.append("interpolation=false")

        if self.filter_analyze:
            properties_lines.append(f"filters={{{self.filter_analyze}}}")
        if self.filter_no_analyze:
            properties_lines.append(f"unfilters={{{self.filter_no_analyze}}}")

        return properties_lines
