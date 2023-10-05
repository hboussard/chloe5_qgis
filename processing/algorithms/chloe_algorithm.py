# -*- coding: utf-8 -*-

"""
***************************************************************************
    ChloeAlgorithm.py
    ---------------------
    Date                 : August 2012
    Copyright            : (C) 2012 by Victor Olaya
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = "Jean-Charles Naud/Alkante"
__date__ = "August 2012"
__copyright__ = "(C) 2012, Victor Olaya"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

import os
from pathlib import Path
import re
from time import gmtime, strftime
from typing import Any

from ..helpers.helpers import (
    file_get_content,
    get_layer_name,
    run_command,
    set_raster_layer_symbology,
)
from ..gui.chloe_algorithm_dialog import ChloeAlgorithmDialog

from processing.tools.system import isWindows, getTempFilename
from qgis.utils import iface

# Heavy overload
from qgis.PyQt.QtCore import QCoreApplication, QLocale
from qgis.PyQt.QtGui import QIcon

from qgis.core import (
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsApplication,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingLayerPostProcessorInterface,
    QgsProject,
    QgsLayerTreeGroup,
)

from qgis.utils import iface

from processing.tools import dataobjects

from ...helpers.constants import CHLOE_JAR_PATH
from ...settings.helpers import check_java_path, get_java_path
from .helpers.constants import OUTPUT_WINDOWS_PATH_DIR, SAVE_PROPERTIES, OUTPUT_RASTER

# END : Heavy overload


class ChloeOutputLayerPostProcessor(QgsProcessingLayerPostProcessorInterface):
    def postProcessLayer(self, layer, context, feedback):
        # print("postProcessing " + layer.name())
        if isinstance(layer, QgsRasterLayer):
            set_raster_layer_symbology(layer=layer, qml_file_name="continuous.qml")


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
            | QgsProcessingAlgorithm.FlagNoThreading
        )  # cannot cancel!

    def get_properties_lines(self) -> "list[str]":
        """get property lines to write in properties file."""
        raise QgsProcessingException(
            f"property lines is not implemented for {self.name()}"
        )

    def set_properties_values(self, parameters, context) -> None:
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

    def get_console_command(self, parameters) -> str:
        """Get full console command to call Chloe
        return arguments : The full command
        Example of return : java -jar bin/chloe-4.0.jar /tmp/distance_paramsrrVtm9.properties
        """

        arguments: list[str] = []

        java_path: Path = get_java_path()

        if not check_java_path(java_path):
            arguments.append("")
        else:
            arguments.append(f'"{str(java_path)}"')

        arguments.append(CHLOE_JAR_PATH)

        if SAVE_PROPERTIES in parameters:
            f_path = parameters[SAVE_PROPERTIES]
        else:
            f_path = getTempFilename(ext="properties")

        if f_path and f_path != "TEMPORARY_OUTPUT":
            # if f_path is defined in widget append to command line to show in command line prompt
            arguments.append(f_path)
        else:
            # if f_path is TEMPORARY get it from the self.output_values (values set when user click on execute algorithm) when Chloe command is executed
            if SAVE_PROPERTIES in self.output_values:
                arguments.append(self.output_values[SAVE_PROPERTIES])

        return " ".join(arguments)

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

        self.set_properties_values(parameters, context)
        self.create_properties_file(self.get_properties_lines())
        command: str = self.get_console_command(parameters)
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
            self.load_output_windows_to_qgis_instance(output_dir=output_dir)

        return results

    def load_output_raster_to_qgis_instance(
        self, output_raster_path: str, context, results: dict[str, Any]
    ):
        """Load output raster results to QGIS instance."""
        raster_layer: QgsRasterLayer = QgsRasterLayer(output_raster_path, "hillshade")
        if not raster_layer.isValid():
            raise QgsProcessingException(
                self.tr("""Cannot load the output in the application""")
            )

        raster_layer_name: str = get_layer_name(
            layer=raster_layer, default_output=self.name()
        )
        set_raster_layer_symbology(layer=raster_layer, qml_file_name="continuous.qml")
        context.temporaryLayerStore().addMapLayer(raster_layer)
        raster_layer_details = QgsProcessingContext.LayerDetails(
            raster_layer_name, context.project(), OUTPUT_RASTER
        )

        context.addLayerToLoadOnCompletion(raster_layer.id(), raster_layer_details)
        results[OUTPUT_RASTER] = raster_layer.id()

    def load_output_windows_to_qgis_instance(
        self,
        output_dir: Path,
        group_name: str = "Window paths",
        group_expanded: bool = False,
        group_checked: bool = False,
        qml_file_name: str = "continuous.qml",
    ):
        """Load output windows paths results to QGIS instance."""
        qgs_project = QgsProject.instance()
        layer_tree = qgs_project.layerTreeRoot()

        # add main group
        root_group: QgsLayerTreeGroup = layer_tree.addGroup(group_name)
        root_group.setExpanded(group_expanded)
        root_group.setItemVisibilityChecked(group_checked)

        for filename in output_dir.iterdir():
            if filename.suffix == ".asc" or filename.suffix == ".tif":
                rlayer = QgsRasterLayer(str(filename), filename.stem)
                if not rlayer.isValid():
                    raise QgsProcessingException(
                        self.tr("""Cannot load the output in the application""")
                    )
                set_raster_layer_symbology(layer=rlayer, qml_file_name=qml_file_name)
                qgs_project.addMapLayer(rlayer, False)
                root_group.addLayer(rlayer)

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
        plugin_path = os.path.dirname(__file__)

        if isWindows():
            context = {
                "plugin_path": "file:///" + (plugin_path + os.sep).replace("/", "\\"),
                "image_path": "file:///"
                + (
                    plugin_path
                    + os.sep
                    + "."
                    + os.sep
                    + "help_algorithm"
                    + os.sep
                    + "images"
                    + os.sep
                ).replace("/", "\\"),
            }
        else:
            context = {
                "plugin_path": plugin_path + os.sep,
                "image_path": plugin_path
                + os.sep
                + "."
                + os.sep
                + "help_algorithm"
                + os.sep
                + "images"
                + os.sep,
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
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        name = self.get_console_command(parameters)[0]
        if name.endswith(".py"):
            name = name[:-3]
        return name

    def tr(self, string, context=""):
        if context == "":
            context = self.__class__.__name__
        return QCoreApplication.translate(context, string)

    def create_projection_file(self, file_path, crs=None, layer_crs=None):
        """Create Projection File"""

        if crs:  # crs given
            crs_output = crs
        elif layer_crs:  # crs from layer
            # Constrution des chemins de sortie des fichiers
            dir_in = os.path.dirname(layer_crs)
            base_in = os.path.basename(layer_crs)
            name_in = os.path.splitext(base_in)[0]
            path_prj_in = dir_in + os.sep + name_in + ".prj"

            if os.path.isfile(path_prj_in):
                crs_output = dataobjects.getObjectFromUri(layer_crs).crs()

            else:  # crs project
                # crs_output = iface.mapCanvas().mapRenderer().destinationCrs()
                crs_output = iface.mapCanvas().mapSettings().destinationCrs()
        else:  # crs project
            # crs_output = iface.mapCanvas().mapRenderer().destinationCrs()
            crs_output = iface.mapCanvas().mapSettings().destinationCrs()

        with open(file_path, "w", encoding="utf-8") as file:
            # b_string = str.encode(crs_output.toWkt())
            file.write(crs_output.toWkt())

    def prepareMultiProjectionFiles(self):
        # === Projection file
        for file in self.outputFilenames:
            baseOut = os.path.basename(file)
            radical = os.path.splitext(baseOut)[0]
            f_prj = self.output_dir + os.sep + radical + ".prj"
            self.create_projection_file(f_prj)

    def parameterRasterAsFilePath(self, parameters, paramName, context) -> str:
        res = self.parameterAsString(parameters, paramName, context)

        if res is None or not res or re.match(r"^[a-zA-Z0-9_]+$", res):
            layer = self.parameterAsRasterLayer(parameters, paramName, context)
            res = layer.dataProvider().dataSourceUri().split("|")[0]

        return res
