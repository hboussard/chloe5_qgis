# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Union

from qgis.core import (
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
)
from processing.tools.system import isWindows

from ...gui.custom_widgets.constants import CUSTOM_WIDGET_DIRECTORY
from ...helpers.helpers import format_path_for_properties_file
from ...gui.custom_parameters.chloe_raster_parameter_file_destination import (
    ChloeRasterParameterFileDestination,
)
from ..chloe_algorithm import ChloeAlgorithm
from ..helpers.constants import (
    CELL_SIZE,
    FIELDS,
    GENERATE_GRID_GROUP_ID,
    GENERATE_GRID_GROUP_NAME,
    METADATA,
    HEIGHT,
    INPUT_FILE_CSV,
    NODATA_VALUE,
    OUTPUT_RASTER,
    SAVE_PROPERTIES,
    WIDTH,
    XMIN,
    YMIN,
)


class FromCSVSingleAlgorithm(ChloeAlgorithm):
    """
    Algorithm generate multiple grids from csv
    """

    def __init__(self):
        super().__init__()

        self.input_csv: str = ""
        self.variables: str = ""
        self.width: Union[int, None] = None
        self.height: Union[int, None] = None
        self.xmin: Union[float, None] = None
        self.ymin: Union[float, None] = None
        self.cellsize: Union[int, None] = None
        self.nodata_value: Union[int, None] = None
        self.output_raster: str = ""

    def initAlgorithm(self, config=None):
        self.init_input_params()
        self.init_algorithm_params()
        self.init_output_params()

    def init_input_params(self):
        """Init input parameters."""
        self.addParameter(
            QgsProcessingParameterFile(
                name=INPUT_FILE_CSV,
                description=self.tr("Input file csv"),
                extension="csv",
                defaultValue=None,
                optional=False,
            )
        )

    def init_algorithm_params(self):
        """Init algorithm parameters."""

        # FIELDS

        csv_fields_param = QgsProcessingParameterString(
            name=FIELDS, description=self.tr("Fields selection"), defaultValue=""
        )
        csv_fields_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.combobox.widget_wrapper.ChloeCsvHeadersComboboxWidgetWrapper",
                    "input_csv": INPUT_FILE_CSV,
                    "parentWidgetConfig": {
                        "linkedParams": [
                            {
                                "paramName": INPUT_FILE_CSV,
                                "refreshMethod": "populate_csv_header_combobox",
                            },
                        ]
                    },
                }
            }
        )

        self.addParameter(csv_fields_param)

        # import raster metadata from file

        import_metadata_param = QgsProcessingParameterString(
            name=METADATA,
            description=self.tr("Import header"),
            defaultValue="",
            optional=True,
        )

        import_metadata_param.setMetadata(
            {
                "widget_wrapper": {
                    "class": f"{CUSTOM_WIDGET_DIRECTORY}.actions.button_import_raster_metadata.widget_wrapper.ChloeImportRasterMetadataButtonWidgetWrapper",
                    "button_title": "Import header",
                },
            }
        )

        self.addParameter(import_metadata_param)
        # WIDTH
        self.addParameter(
            QgsProcessingParameterNumber(
                name=WIDTH,
                description=self.tr("Columns count"),
                minValue=0,
                defaultValue=100,
            )
        )
        # HEIGHT
        self.addParameter(
            QgsProcessingParameterNumber(
                name=HEIGHT,
                description=self.tr("Rows count"),
                minValue=0,
                defaultValue=100,
            )
        )
        # XMIN
        self.addParameter(
            QgsProcessingParameterNumber(
                name=XMIN,
                description=self.tr("X bottom left corner coordinate"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=YMIN,
                type=QgsProcessingParameterNumber.Double,
                description=self.tr("Y bottom left corner coordinate"),
                defaultValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=CELL_SIZE,
                type=QgsProcessingParameterNumber.Double,
                description=self.tr("Cell size"),
                defaultValue=1.0,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=NODATA_VALUE,
                description=self.tr("Value if no-data"),
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
        return "single from csv"

    def displayName(self):
        return self.tr("Generate single raster from CSV data file")

    def group(self):
        return self.tr(GENERATE_GRID_GROUP_NAME)

    def groupId(self):
        return GENERATE_GRID_GROUP_ID

    def commandName(self):
        return "from csv"

    def set_properties_input_values(self, parameters, context, feedback):
        """Set input values."""

        self.input_csv = self.parameterAsString(parameters, INPUT_FILE_CSV, context)

    def set_properties_algorithm_values(self, parameters, context, feedback):
        """Set algorithm parameters."""

        self.variables = self.parameterAsString(parameters, FIELDS, context)
        self.width = self.parameterAsInt(parameters, WIDTH, context)
        self.height = self.parameterAsInt(parameters, HEIGHT, context)
        self.xmin = self.parameterAsDouble(parameters, XMIN, context)
        self.ymin = self.parameterAsDouble(parameters, YMIN, context)
        self.cellsize = self.parameterAsInt(parameters, CELL_SIZE, context)
        self.nodata_value = self.parameterAsInt(parameters, NODATA_VALUE, context)

    def set_properties_output_values(self, parameters, context, feedback):
        """Set output values."""

        self.output_raster = self.parameterAsOutputLayer(
            parameters, OUTPUT_RASTER, context
        )
        self.create_projection_file(output_path_raster=Path(self.output_raster))
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

        properties_lines.append("treatment=raster_from_csvs")
        properties_lines.append(
            format_path_for_properties_file(f"input_csv={self.input_csv}", isWindows())
        )
        properties_lines.append(
            format_path_for_properties_file(
                f"output_raster={self.output_raster}", isWindows()
            )
        )
        properties_lines.append(f"variables={{{self.variables}}}")
        properties_lines.append(f"width={str(self.width)}")
        properties_lines.append(f"height={str(self.height)}")
        properties_lines.append(f"xmin={str(self.xmin)}")
        properties_lines.append(f"ymin={str(self.ymin)}")
        properties_lines.append(f"cellsize={str(self.cellsize)}")
        properties_lines.append(f"nodata_value={str(self.nodata_value)}")

        return properties_lines
