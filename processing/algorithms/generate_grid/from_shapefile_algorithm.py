from typing import Union
from pathlib import Path
from qgis.core import (
    QgsProcessingParameterNumber,
    QgsProcessingParameterFileDestination,
    QgsRectangle,
    QgsVectorLayer,
    QgsProcessingParameterExtent,
    QgsProcessingException,
    QgsMapLayer,
    QgsProcessingParameterField,
)
from processing.tools.system import isWindows

from ...gui.custom_widgets.constants import CUSTOM_WIDGET_DIRECTORY
from ...helpers.helpers import format_path_for_properties_file
from ...gui.custom_parameters.chloe_raster_parameter_file_destination import (
    ChloeRasterParameterFileDestination,
)
from ...gui.custom_parameters.chloe_shapefile_parameter_file_input import (
    ChloeShapefileParameterFileInput,
)
from ..chloe_algorithm import ChloeAlgorithm
from ..helpers.constants import (
    CELL_SIZE,
    EXTENT,
    FIELD,
    FILL_VALUE,
    GENERATE_GRID_GROUP_ID,
    GENERATE_GRID_GROUP_NAME,
    INPUT_SHAPEFILE,
    NODATA_VALUE,
    OUTPUT_RASTER,
    SAVE_PROPERTIES,
)


class FromShapefileAlgorithm(ChloeAlgorithm):
    """
    Algorithm generate grid from shapefile
    """

    def __init__(self):
        super().__init__()
        self.input_shp: str = ""
        self.field: str = ""
        self.cellsize: Union[float, None] = None
        self.extent: Union[QgsRectangle, None] = None
        self.nodata_value: Union[int, None] = None
        self.fill_value: Union[float, None] = None
        self.output_raster: str = ""

    def initAlgorithm(self, config=None):
        self.init_input_params()
        self.init_algorithm_params()
        self.init_output_params()

    def init_input_params(self):
        """Init input parameters."""

        input_raster_param = ChloeShapefileParameterFileInput(
            name=INPUT_SHAPEFILE, description=self.tr("Input vector layer")
        )

        input_raster_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.layer_input.widget_wrapper.ChloeVectorInputWidgetWrapper"
                }
            }
        )
        self.addParameter(input_raster_param)

    def init_algorithm_params(self):
        """Init algorithm parameters."""

        self.addParameter(
            QgsProcessingParameterField(
                name=FIELD,
                description=self.tr("Field selection"),
                parentLayerParameterName=INPUT_SHAPEFILE,
                type=QgsProcessingParameterField.Any,
                optional=False,
            )
        )

        # EXTENT
        self.addParameter(
            QgsProcessingParameterExtent(
                name=EXTENT, description=self.tr("Region extent")
            )
        )
        # CELL SIZE
        self.addParameter(
            QgsProcessingParameterNumber(
                name=CELL_SIZE,
                description=self.tr("Cell size"),
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                defaultValue=1.0,
            )
        )
        # NODATA VALUE
        self.addParameter(
            QgsProcessingParameterNumber(
                name=NODATA_VALUE,
                description=self.tr("Nodata value"),
                type=QgsProcessingParameterNumber.Integer,
                minValue=-9999,
                defaultValue=-1,
            )
        )
        # FILL VALUE
        self.addParameter(
            QgsProcessingParameterNumber(
                name=FILL_VALUE,
                description=self.tr("Fill value"),
                type=QgsProcessingParameterNumber.Integer,
                minValue=-9999,
                defaultValue=-1,
            )
        )

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
        return "From shapefile"

    def displayName(self):
        return self.tr("From shapefile layer")

    def group(self):
        return self.tr(GENERATE_GRID_GROUP_NAME)

    def groupId(self):
        return GENERATE_GRID_GROUP_ID

    def commandName(self):
        return "fromshapefile"

    def checkParameterValues(self, parameters, context):
        """Override checkParameterValues base class method.
        This override is needed because QgsProcessingParameterVectorLayer does not support file filters on the selection combobox for existing layers in the canvas.
        Users can select any vector layer loaded in the canvas, regardless of the file extension. This method checks if the selected vector layer is a supported file extension.
        """

        input_vector: QgsVectorLayer = self.parameterAsVectorLayer(
            parameters, INPUT_SHAPEFILE, context
        )
        if input_vector and input_vector.isValid():
            input_vector_path: Path = Path(input_vector.dataProvider().dataSourceUri())
            input_vector_file_extension: str = input_vector_path.suffix.lower()[1:]

            if input_vector_file_extension != "shp":
                return False, self.tr(
                    f"The selected vector layer type {input_vector_file_extension} is not supported. Please select a Shapefile."
                )

        # If these parameters are valid, call the parent class's checkParameterValues method for the rest
        return super().checkParameterValues(parameters, context)

    def set_properties_input_values(self, parameters, context, feedback):
        """Set input values."""

        layer: Union[QgsMapLayer, None] = self.parameterAsLayer(
            parameters, INPUT_SHAPEFILE, context
        )
        if layer is None:
            raise QgsProcessingException(
                self.invalid_source_error(parameters, INPUT_SHAPEFILE)
            )
        self.input_shp = layer.source()

    def set_properties_algorithm_values(self, parameters, context, feedback):
        """Set algorithm parameters."""

        self.field = self.parameterAsString(parameters, FIELD, context)
        self.cellsize = self.parameterAsDouble(parameters, CELL_SIZE, context)
        self.extent = self.parameterAsExtent(parameters, EXTENT, context)
        self.nodata_value = self.parameterAsInt(parameters, NODATA_VALUE, context)
        self.fill_value = self.parameterAsDouble(parameters, FILL_VALUE, context)

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""

        self.output_raster = self.parameterAsOutputLayer(
            parameters, OUTPUT_RASTER, context
        )

        self.set_output_parameter_value(OUTPUT_RASTER, self.output_raster)

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

        properties_lines.append("treatment=raster_from_shapefile")
        properties_lines.append(
            format_path_for_properties_file(
                f"input_shapefile={self.input_shp}", isWindows()
            )
        )
        properties_lines.append(
            format_path_for_properties_file(
                f"output_raster={self.output_raster}", isWindows()
            )
        )
        properties_lines.append(f"attribute={self.field}")
        if self.extent is not None:
            properties_lines.append(f"xmin={str(self.extent.xMinimum())}")
            properties_lines.append(f"xmax={str(self.extent.xMaximum())}")
            properties_lines.append(f"ymin={str(self.extent.yMinimum())}")
            properties_lines.append(f"ymax={str(self.extent.yMaximum())}")
        properties_lines.append(f"cellsize={str(self.cellsize)}")
        properties_lines.append(f"nodata_value={str(self.nodata_value)}")
        properties_lines.append(f"fill_value={self.fill_value}")

        return properties_lines
