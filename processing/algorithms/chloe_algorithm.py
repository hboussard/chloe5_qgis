# -*- coding: utf-8 -*-
import os
from pathlib import Path
from re import search, IGNORECASE, match
from time import gmtime, strftime
from typing import Any
from qgis.PyQt.QtCore import QCoreApplication, QLocale
from qgis.PyQt.QtGui import QIcon

from qgis.core import (
    QgsProcessingContext,
    QgsRasterLayer,
    QgsProcessingAlgorithm,
    QgsProcessingException,
)

from qgis.utils import iface

from processing.tools.system import getTempFilename

from ...helpers.helpers import (
    RasterLoadConfig,
    load_rasters_from_directory_to_qgis_instance,
    set_raster_layer_symbology,
    get_layer_name,
)
from ...helpers.helpers import run_command, get_console_command
from ...helpers.constants import CHLOE_PLUGIN_PATH

from ..helpers.helpers import (
    file_get_content,
)
from ..styles.constants import STYLES_PATH
from ..gui.chloe_algorithm_dialog import ChloeAlgorithmDialog

from .helpers.constants import OUTPUT_WINDOWS_PATH_DIR, SAVE_PROPERTIES, OUTPUT_RASTER


class ChloeAlgorithm(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.output_values: dict[str, Any] = {}

    def icon(self):
        iconPath = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "images", "chloe_icon.png")
        )
        return QIcon(iconPath)

    def tags(self):
        return ["chloe", self.commandName()]

    # def svgIconPath(self):
    #    return QgsApplication.iconPath("providerChloe.svg")

    def createInstance(self):
        return self.__class__()

    def createCustomParametersWidget(self, parent):
        return ChloeAlgorithmDialog(self, parent=parent)

    def flags(self):
        return (
            QgsProcessingAlgorithm.FlagSupportsBatch
            | QgsProcessingAlgorithm.FlagCanCancel
        )

    def get_properties_lines(self) -> "list[str]":
        """get property lines to write in properties file."""
        raise QgsProcessingException(
            f"property lines is not implemented for {self.name()}"
        )

    def set_properties_values(self, parameters, context, feedback) -> None:
        """set properties values."""
        raise QgsProcessingException(
            f"set properties values is not implemented for {self.name()}"
        )

    def create_properties_file(self, lines: "list[str]"):
        """Create Properties File."""
        if self.output_values[SAVE_PROPERTIES]:
            s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            try:
                with open(
                    self.output_values[SAVE_PROPERTIES], "w+", encoding="utf-8"
                ) as file:
                    file.write(f"#{s_time}\n")
                    for line in lines:
                        file.write(f"{line}\n")
            except OSError as exc:
                raise QgsProcessingException(
                    self.tr(
                        f"Cannot create properties file {self.output_values[SAVE_PROPERTIES]}"
                    )
                ) from exc

    def get_properties_file_path(self, parameters) -> str:
        """Get properties file path."""

        properties_file_path: str = ""

        if SAVE_PROPERTIES in parameters:
            properties_file_param_value: str = parameters[SAVE_PROPERTIES]
        else:
            properties_file_param_value = getTempFilename(ext="properties")

        if (
            properties_file_param_value
            and properties_file_param_value != "TEMPORARY_OUTPUT"
        ):
            # if f_path is defined in widget append to command line to show in command line prompt
            properties_file_path = properties_file_param_value
        else:
            # if f_path is TEMPORARY get it from the self.output_values (values set when user click on execute algorithm) when Chloe command is executed
            if SAVE_PROPERTIES in self.output_values:
                properties_file_path = self.output_values[SAVE_PROPERTIES]

        return properties_file_path

    def set_output_parameter_value(
        self, parameter_name: str, parameter_value: Any
    ) -> None:
        """
        Sets the value of the specified output parameter.

        Args:
            name (str): The name of the output parameter to set.
            value (Any): The value to assign to the output parameter.

        Returns:
            None
        """
        self.output_values[parameter_name] = parameter_value

    def processAlgorithm(self, parameters, context, feedback):
        """
        Process the algorithm.

        Args:
            parameters (dict): A dictionary of input parameters.
            context (QgsProcessingContext): The processing context.
            feedback (QgsProcessingFeedback): The feedback object.

        Returns:
            dict: A dictionary of output parameters.
        """

        self.set_properties_values(parameters, context, feedback)
        self.create_properties_file(self.get_properties_lines())
        command: str = get_console_command(self.get_properties_file_path(parameters))
        run_command(command_line=command, feedback=feedback)

        results: dict[str, Any] = {}
        for definition in self.outputDefinitions():
            if definition.name() in parameters:
                results[definition.name()] = parameters[definition.name()]
        for param_name, param_value in self.output_values.items():
            results[param_name] = param_value

        if OUTPUT_RASTER in parameters:
            # add custom style to OUTPUT_ASC parameter if is to load on completion
            output_raster_path: str = self.output_values[OUTPUT_RASTER]
            load_on_completion = (
                output_raster_path in context.layersToLoadOnCompletion()
            )

            if load_on_completion:
                self.load_output_raster_to_qgis_instance(
                    output_raster_path=output_raster_path,
                    context=context,
                    results=results,
                )

        if OUTPUT_WINDOWS_PATH_DIR in parameters:
            output_dir: Path = Path(self.output_values[OUTPUT_WINDOWS_PATH_DIR])
            output_dir_rasters_config: RasterLoadConfig = RasterLoadConfig(
                raster_directory=output_dir,
                group_name="Windows_paths",
                qml_file_path=STYLES_PATH / "continuous.qml",
            )
            load_rasters_from_directory_to_qgis_instance(output_dir_rasters_config)

        return results

    def load_output_raster_to_qgis_instance(
        self, output_raster_path: str, context, results: dict[str, Any]
    ) -> None:
        """
        Load output raster results to QGIS instance.

        Args:
            output_raster_path (str): The path to the output raster.
            context: The processing context.
            results (dict[str, Any]): The dictionary of results.

        Raises:
            QgsProcessingException: If the output raster cannot be loaded in the application.
        """
        raster_layer: QgsRasterLayer = QgsRasterLayer(output_raster_path, "hillshade")
        if not raster_layer.isValid():
            raise QgsProcessingException(
                self.tr("""Cannot load the output in the application""")
            )

        raster_layer_name: str = get_layer_name(
            layer=raster_layer, default_output=self.name()
        )

        set_raster_layer_symbology(
            layer=raster_layer, qml_file_path=STYLES_PATH / "continuous.qml"
        )
        context.temporaryLayerStore().addMapLayer(raster_layer)
        raster_layer_details = QgsProcessingContext.LayerDetails(
            raster_layer_name, context.project(), OUTPUT_RASTER
        )

        context.addLayerToLoadOnCompletion(raster_layer.id(), raster_layer_details)
        results[OUTPUT_RASTER] = raster_layer.id()

    def helpUrl(self):
        localeName = QLocale.system().name()
        helpFilename = f"{self.name()}_{localeName}.html"
        helpfile = f"{os.path.dirname(__file__)}{os.sep}.{os.sep}help_algorithm{os.sep}{helpFilename}"
        return helpfile

    def shortHelpString(self):
        return self.helpString()

    def helpString(self):
        """Generation de l'onglet help"""
        helpfile = self.helpUrl()
        plugin_path: Path = CHLOE_PLUGIN_PATH

        context = {
            "plugin_path": f"file://{plugin_path.as_posix()}/",
            "image_path": f"file://{plugin_path / 'processing' / 'algorithms' / 'documentation' / 'images'}/",
        }

        # print(helpfile)
        content = file_get_content(helpfile, encoding="utf-8", context=context)

        if not (content is None):
            return content
        else:
            return self.tr("No help available for this algorithm")

    def commandName(self):
        parameters = {}
        for param in self.parameterDefinitions():
            parameters[param.name()] = "1"
        name = get_console_command(self.get_properties_file_path(parameters))[0]
        if name.endswith(".py"):
            name = name[:-3]
        return name

    def tr(self, string, context=""):
        if context == "":
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)

    def create_projection_file(self, output_path_raster: Path):
        """Create Projection File"""
        if not search(r"asc", output_path_raster.suffix, IGNORECASE):
            return
        f_prj = str(output_path_raster.parent / f"{output_path_raster.stem}.prj")
        crs_output = iface.mapCanvas().mapSettings().destinationCrs()
        with open(f_prj, "w", encoding="utf-8") as file:
            # b_string = str.encode(crs_output.toWkt())
            file.write(crs_output.toWkt())

    def parameterRasterAsFilePath(self, parameters, paramName, context) -> str:
        res = self.parameterAsString(parameters, paramName, context)

        if res is None or not res or match(r"^[a-zA-Z0-9_]+$", res):
            layer = self.parameterAsRasterLayer(parameters, paramName, context)
            res = layer.dataProvider().dataSourceUri().split("|")[0]

        return res
