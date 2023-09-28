# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Chole
                                 A QGIS plugin
 description
                              -------------------
        begin                : 2017-10-17
        author : Jean-Charles Naud, Olivier Bedel, Hugues Boussard

        email                : hugues.boussard at inra.fr
 ***************************************************************************/

"""

from pathlib import Path
from ...gui.custom_parameters.chloe_raster_parameter_file_destination import (
    ChloeRasterParameterFileDestination,
)
from ...gui.custom_parameters.chloe_csv_parameter_file_destination import (
    ChloeCSVParameterFileDestination,
)

from ...gui.custom_widgets.constants import CUSTOM_WIDGET_DIRECTORY
from ...helpers.helpers import (
    convert_to_odd,
    enum_to_list,
    format_string,
    get_enum_order_as_int,
)


from qgis.core import (
    QgsProcessingParameterDefinition,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFileDestination,
)

from processing.tools.system import isWindows

from ..chloe_algorithm import ChloeAlgorithm
from ..helpers.constants import (
    ANALYZE_TYPE,
    DELTA_DISPLACEMENT,
    DISTANCE_FRICTION,
    DISTANCE_FUNCTION,
    FAST,
    FILTER_ANALYZE,
    FILTER_NO_ANALYZE,
    FRICTION_FILE,
    INPUT_RASTER,
    INTERPOLATE_VALUES_BOOL,
    MAXIMUM_RATE_MISSING_VALUES,
    METRICS,
    OUTPUT_RASTER,
    OUTPUT_CSV,
    SAVE_PROPERTIES,
    WINDOW_SHAPE,
    WINDOW_SIZES,
)
from ..helpers.constants_metrics import TYPES_OF_METRICS
from ..helpers.enums import AnalyzeType, WindowShapeType


class SlidingAlgorithm(ChloeAlgorithm):
    """Algorithm sliding."""

    def __init__(self):
        super().__init__()

    def initAlgorithm(self, config=None):
        # === INPUT PARAMETERS ===

        # algorithm is fast
        fast_param: QgsProcessingParameterBoolean = QgsProcessingParameterBoolean(
            name=FAST, description=self.tr("Fast"), defaultValue=False
        )
        fast_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.checkbox_update_state.widget_wrapper.ChloeCheckboxUpdateStateWidgetWrapper",
                    "dependantWidgetConfig": [
                        {"paramName": ANALYZE_TYPE, "enableValue": False},
                    ],
                }
            }
        )

        self.addParameter(fast_param)

        # INPUT ASC
        inputAscParam = QgsProcessingParameterRasterLayer(
            name=INPUT_RASTER, description=self.tr("Input raster layer")
        )

        inputAscParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.raster_input.widget_wrapper.ChloeAscRasterWidgetWrapper"
                }
            }
        )
        self.addParameter(inputAscParam)

        # METRICS

        metricsParam = QgsProcessingParameterString(
            name=METRICS, description=self.tr("Select metrics")
        )

        metricsParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.double_combobox.widget_wrapper.ChloeDoubleComboboxWidgetWrapper",
                    "dictValues": TYPES_OF_METRICS,
                    "initialValue": "diversity metrics",
                    "rasterLayerParamName": INPUT_RASTER,
                    "parentWidgetConfig": {
                        "linkedParams": [
                            {
                                "paramName": INPUT_RASTER,
                                "refreshMethod": "refreshMappingCombobox",
                            },
                        ]
                    },
                }
            }
        )

        self.addParameter(metricsParam)

        ###### ADVANCED PARAMETERS ######

        # WINDOW SHAPE

        windowShapeParam = QgsProcessingParameterEnum(
            name=WINDOW_SHAPE,
            description=self.tr("Window shape"),
            options=enum_to_list(WindowShapeType),
        )

        windowShapeParam.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.enum_update_state.widget_wrapper.ChloeEnumUpdateStateWidgetWrapper",
                    "dependantWidgetConfig": [
                        {
                            "paramName": FRICTION_FILE,
                            "enableValue": get_enum_order_as_int(
                                WindowShapeType.FUNCTIONAL
                            ),
                        }
                    ],
                }
            }
        )

        windowShapeParam.setFlags(
            windowShapeParam.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(windowShapeParam)

        # FRICTION FILE (OPTIONAL)

        friction_file = QgsProcessingParameterFile(
            name=FRICTION_FILE, description=self.tr("Friction file"), optional=True
        )
        friction_file.setFileFilter("GeoTIFF (*.tif *.TIF);; ASCII (*.asc *.ASC)")
        friction_file.setFlags(
            friction_file.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )

        self.addParameter(friction_file)

        # ANALYZE TYPE

        analyze_type_param = QgsProcessingParameterEnum(
            name=ANALYZE_TYPE,
            description=self.tr("Analyze type"),
            options=enum_to_list(AnalyzeType),
        )

        # analyze_type_param.setUsesStaticStrings(True)

        analyze_type_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.enum_update_state.widget_wrapper.ChloeEnumUpdateStateWidgetWrapper",
                    "dependantWidgetConfig": [
                        {
                            "paramName": DISTANCE_FUNCTION,
                            "enableValue": get_enum_order_as_int(
                                AnalyzeType.WEIGHTED_DISTANCE
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
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.values_selection.widget_wrapper.ChloeValuesWidgetWrapper"
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
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.values_selection.widget_wrapper.ChloeValuesWidgetWrapper"
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

        # WINDOW SIZE
        window_size_parameter = QgsProcessingParameterNumber(
            name=WINDOW_SIZES,
            description=self.tr("Windows sizes (pixels)"),
            defaultValue=3,
            minValue=3,
        )

        self.addParameter(window_size_parameter)

        # === OUTPUT PARAMETERS ===

        self.addParameter(
            ChloeCSVParameterFileDestination(
                name=OUTPUT_CSV, description=self.tr("Output csv")
            )
        )

        raster_output_parameter = ChloeRasterParameterFileDestination(
            name=OUTPUT_RASTER, description=self.tr("Output Raster")
        )
        self.addParameter(raster_output_parameter, createOutput=True)

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
        return self.tr("landscape metrics")

    def groupId(self):
        return "landscapemetrics"

    def commandName(self):
        return "java"

    def PreRun(self, parameters, context, feedback, executing=True):
        """Here is where the processing itself takes place."""

        # === INPUT
        self.input_raster = self.parameterRasterAsFilePath(
            parameters, INPUT_RASTER, context
        )

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

        # === OUTPUT
        self.output_csv = self.parameterAsOutputLayer(parameters, OUTPUT_CSV, context)
        self.output_raster = self.parameterAsOutputLayer(
            parameters, OUTPUT_RASTER, context
        )
        self.setOutputValue(OUTPUT_CSV, self.output_csv)
        self.setOutputValue(OUTPUT_RASTER, self.output_raster)

        output_path_raster: Path = Path(self.output_raster)
        dir_out_raster: Path = output_path_raster.parent
        base_out_raster: str = output_path_raster.name
        name_out_raster: str = output_path_raster.stem

        # === SAVE_PROPERTIES

        f_save_properties: str = self.parameterAsString(
            parameters, SAVE_PROPERTIES, context
        )

        self.setOutputValue(SAVE_PROPERTIES, f_save_properties)

        print(self.output_values)
        # === Properties files
        self.createProperties()

        # === Projection file
        f_prj: str = str(dir_out_raster / f"{name_out_raster}.prj")
        self.createProjectionFile(f_prj)

    def createProperties(self):
        """Create Properties File."""
        properties_lines: list[str] = []

        properties_lines.append("treatment=sliding\n")
        properties_lines.append(
            format_string(
                input_string=f"input_raster={self.input_raster}\n",
                is_windows_system=isWindows(),
            )
        )
        properties_lines.append(
            format_string(
                input_string=f"output_csv={self.output_csv}\n",
                is_windows_system=isWindows(),
            )
        )
        properties_lines.append(
            format_string(
                input_string=f"output_raster={self.output_raster}\n",
                is_windows_system=isWindows(),
            )
        )

        properties_lines.append(
            f"sizes={{{str(convert_to_odd(input_integer=self.window_sizes))}}}\n"
        )
        properties_lines.append(
            f"maximum_nodata_value_rate={str(self.maximum_rate_missing_values)}\n"
        )

        if self.analyze_type == "weighted distance":
            properties_lines.append(f"distance_function={str(self.distance_formula)}\n")

        properties_lines.append(f"metrics={{{self.metrics}}}\n")
        properties_lines.append(f"delta_displacement={str(self.delta_displacement)}\n")
        properties_lines.append(f"shape={str(self.window_shape)}\n")
        if self.window_shape == "FUNCTIONAL":
            properties_lines.append(f"friction={self.friction_file}\n")

        if self.b_interpolate_values:
            properties_lines.append("interpolation=true\n")
        else:
            properties_lines.append("interpolation=false\n")

        if self.filter_analyze:
            properties_lines.append(f"filters={{{self.filter_analyze}}}\n")
        if self.filter_no_analyze:
            properties_lines.append(f"unfilters={{{self.filter_no_analyze}}}\n")

        # Writing the second part of the properties file
        if self.output_csv:
            properties_lines.append("export_csv=true\n")
        else:
            properties_lines.append("export_csv=false\n")

        if self.output_raster:
            properties_lines.append("export_ascii=true\n")
        else:
            properties_lines.append("export_ascii=false\n")

        self.createPropertiesFile(properties_lines)
