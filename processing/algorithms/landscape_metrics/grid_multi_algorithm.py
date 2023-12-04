from qgis.core import (
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterFolderDestination,
)

from processing.tools.system import isWindows

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
    LANDSCAPE_METRICS_MULTI_GROUP_ID,
    LANDSCAPE_METRICS_MULTI_GROUP_NAME,
    MAXIMUM_RATE_MISSING_VALUES,
    METRICS,
    OUTPUT_DIR,
    SAVE_PROPERTIES,
)


class GridMultiAlgorithm(ChloeAlgorithm):
    """Grid multi algorithm."""

    def __init__(self):
        super().__init__()

        # properties values

        self.input_raster: str = ""
        self.grid_sizes: str = ""
        self.maximum_rate_missing_values: int = 100
        self.metrics: str = ""
        self.output_folder: str = ""

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

        # GRID SIZE
        grid_size_param = QgsProcessingParameterString(
            name=GRID_SIZES, description=self.tr("Grid sizes (pixels)")
        )

        grid_size_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.number_list_selector.widget_wrapper.ChloeIntListSelectorWidgetWrapper",
                    "default_value": 2,
                    "max_value": 100001,
                    "min_value": 2,
                }
            }
        )
        self.addParameter(grid_size_param)

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
        output_folder_parameter = QgsProcessingParameterFolderDestination(
            name=OUTPUT_DIR,
            description=self.tr("Output windows folder"),
        )
        self.addParameter(output_folder_parameter)

        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=SAVE_PROPERTIES,
                description=self.tr("Properties file"),
                fileFilter="Properties (*.properties)",
            )
        )

    def name(self):
        return "grid multi"

    def displayName(self):
        return self.tr("grid multi")

    def group(self):
        return self.tr(LANDSCAPE_METRICS_MULTI_GROUP_NAME)

    def groupId(self):
        return LANDSCAPE_METRICS_MULTI_GROUP_ID

    def commandName(self):
        return "grid multi"

    def set_properties_input_values(self, parameters, context, feedback):
        """Set input values."""
        self.input_raster = self.parameterRasterAsFilePath(
            parameters, INPUT_RASTER, context
        )

    def set_properties_algorithm_values(self, parameters, context, feedback):
        """Set algorithm parameters."""
        self.grid_sizes = self.parameterAsString(parameters, GRID_SIZES, context)
        self.maximum_rate_missing_values = self.parameterAsInt(
            parameters, MAXIMUM_RATE_MISSING_VALUES, context
        )
        self.metrics = self.parameterAsString(parameters, METRICS, context)

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""
        self.output_folder = self.parameterAsString(parameters, OUTPUT_DIR, context)
        self.set_output_parameter_value(OUTPUT_DIR, self.output_folder)

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

        properties_lines.append(
            format_path_for_properties_file(
                input_string=f"output_folder={self.output_folder}",
                is_windows_system=isWindows(),
            )
        )
        return properties_lines
