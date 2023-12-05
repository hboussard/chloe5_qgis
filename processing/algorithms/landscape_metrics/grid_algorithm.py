from qgis.core import (
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
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
    format_path_for_properties_file,
)
from ..chloe_algorithm import ChloeAlgorithm
from ..helpers.constants import (
    GRID_SIZES,
    INPUT_RASTER,
    LANDSCAPE_METRICS_GROUP_ID,
    LANDSCAPE_METRICS_GROUP_NAME,
    MAXIMUM_RATE_MISSING_VALUES,
    METRICS,
    OUTPUT_CSV,
    OUTPUT_RASTER,
    SAVE_PROPERTIES,
)


class GridAlgorithm(ChloeAlgorithm):
    """Grid algorithm"""

    def __init__(self):
        super().__init__()

        # properties values

        self.input_raster: str = ""
        self.grid_sizes: int = 2
        self.maximum_rate_missing_values: int = 100
        self.metrics: str = ""
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

        # GRID SIZE
        self.addParameter(
            QgsProcessingParameterNumber(
                name=GRID_SIZES,
                description=self.tr("Grid size (pixels)"),
                defaultValue=2,
                minValue=2,
            )
        )

        # MAXIMUM RATE MISSING VALUES
        self.addParameter(
            QgsProcessingParameterNumber(
                name=MAXIMUM_RATE_MISSING_VALUES,
                description=self.tr("Maximum rate of mising values"),
                minValue=0,
                maxValue=100,
                defaultValue=100,
            )
        )

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
        return "grid"

    def displayName(self):
        return self.tr("grid")

    def group(self):
        return self.tr(LANDSCAPE_METRICS_GROUP_NAME)

    def groupId(self):
        return LANDSCAPE_METRICS_GROUP_ID

    def commandName(self):
        return "grid"

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
        self.grid_sizes = self.parameterAsInt(parameters, GRID_SIZES, context)
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
        properties_lines.append("treatment=grid")
        properties_lines.append(
            format_path_for_properties_file(
                input_string=f"input_raster={self.input_raster}",
                is_windows_system=isWindows(),
            )
        )
        properties_lines.append(f"sizes={str(self.grid_sizes)}")
        properties_lines.append(
            f"maximum_rate_nodata_value={str(self.maximum_rate_missing_values)}"
        )
        properties_lines.append(f"metrics={{{self.metrics}}}")
        if self.output_csv:
            properties_lines.append(
                format_path_for_properties_file(
                    input_string=f"output_csv={self.output_csv}",
                    is_windows_system=isWindows(),
                )
            )

        properties_lines.append(
            format_path_for_properties_file(
                input_string=f"output_raster={self.output_raster}",
                is_windows_system=isWindows(),
            )
        )
        return properties_lines
