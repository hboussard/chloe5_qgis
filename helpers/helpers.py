from dataclasses import dataclass, field
import os

from pathlib import Path
import signal
import platform
from typing import Protocol, Union
from re import search
from subprocess import Popen, PIPE, STDOUT, DEVNULL
import numpy as np
from math import floor
from osgeo import gdal
from qgis.utils import iface
from qgis.core import (
    QgsRasterLayer,
    QgsRasterBandStats,
    QgsMessageLog,
    Qgis,
    QgsSingleBandPseudoColorRenderer,
    QgsRasterShader,
    QgsColorRampShader,
    QgsProcessingFeedback,
    QgsProject,
    QgsLayerTreeGroup,
)
from .constants import (
    CHLOE_WORKING_DIRECTORY_PATH,
    CHLOE_JAR_PATH,
    CHLOE_RASTER_FILE_EXTENSIONS,
)
from ..settings.helpers import get_java_path, check_java_path


class CustomFeedback(Protocol):
    def pushInfo(self, message: str) -> None:
        ...

    def pushCommandInfo(self, message: str) -> None:
        ...

    def pushConsoleInfo(self, message: str) -> None:
        ...

    def setProgress(self, progress: float) -> None:
        ...

    def isCanceled(self) -> bool:
        ...


def run_command(
    command_line: str,
    feedback: Union[CustomFeedback, None] = None,
) -> None:
    """
    Runs a command line command and logs the output.

    Args:
        command_line (str): The command line command to run.
        feedback (Union[CustomFeedback, None], optional): The feedback object to use for logging. Defaults to None.
    """

    if feedback is None:
        feedback = QgsProcessingFeedback()

    QgsMessageLog.logMessage(command_line, "Processing", Qgis.Info)
    feedback.pushInfo("CHLOE command:")
    feedback.pushCommandInfo(command_line)
    feedback.pushInfo("CHLOE command output:")

    success = False
    retry_count = 0
    while not success:
        loglines = []
        loglines.append("CHLOE execution console output")
        try:
            with Popen(
                command_line,
                shell=True,
                stdout=PIPE,
                stdin=DEVNULL,
                stderr=STDOUT,
                # universal_newlines=True,
                cwd=str(CHLOE_WORKING_DIRECTORY_PATH),
            ) as process:
                success = True

                for byte_line in process.stdout:
                    if feedback.isCanceled():
                        if platform.system() == "Windows":
                            os.call(
                                [
                                    "taskkill",
                                    "/F",
                                    "/T",
                                    "/PID",
                                    str(process.pid),
                                ]
                            )
                        else:
                            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        return
                    line = byte_line.decode("utf8", errors="backslashreplace").replace(
                        "\r", ""
                    )
                    feedback.pushConsoleInfo(line)
                    loglines.append(line)
                    # get progress value from line using regex
                    progress_value: float = get_progress_value_from_line(line)
                    feedback.setProgress(progress_value)

        except IOError as error:
            if retry_count < 5:
                # print('retry ' + str(retry_count))
                retry_count += 1
            else:
                raise IOError(
                    str(error)
                    + f'\nTried 5 times without success. Last iteration stopped after reading {len(loglines)} line(s).\nLast line(s):\n{",".join(loglines[-10:])}'
                ) from error

        QgsMessageLog.logMessage("\n".join(loglines), "Processing", Qgis.Info)


def get_progress_value_from_line(line: str) -> float:
    """Get progress value from line using regex"""
    progress: float = 0.0

    re_percent = search(r"^#(100|\d{1,2})$", line)

    if re_percent:
        try:
            float(re_percent.group(1))
        except ValueError:
            QgsMessageLog.logMessage(
                f"Impossible de convertir en float le pourcentage de progression : {re_percent.group(1)}",
            )
    return progress


def get_console_command(properties_file_path: str) -> str:
    """Get full console command to call Chloe
    Example of return : java -jar bin/chloe-4.0.jar /tmp/distance_paramsrrVtm9.properties
    """

    arguments: list[str] = []

    java_path: Path = get_java_path()

    if not check_java_path(java_path):
        arguments.append("")
    else:
        arguments.append(f'"{str(java_path)}"')

    arguments.append(CHLOE_JAR_PATH)
    arguments.append(properties_file_path)

    return " ".join(arguments)


def set_raster_layer_symbology(layer: QgsRasterLayer, qml_file_path: Path) -> None:
    """
    Set the layer symbology from a qml file. Adjust the symbology to equal intervals from the raster layer statistics.

    Args:
        layer (QgsRasterLayer): The raster layer to set the symbology for.
        qml_file_name (str): The name of the qml file containing the symbology.

    Returns:
        None
    """

    if not qml_file_path.exists() or qml_file_path == Path():
        error_message: str = f"Fichier qml non trouvé : {qml_file_path}"
        QgsMessageLog.logMessage(error_message, level=Qgis.Critical)
        iface.messageBar().pushMessage(
            "Erreur",
            error_message,
            level=Qgis.Critical,
        )
        return

    if not layer.isValid():
        error_message: str = f"Fichier raster non valide : {layer.source()} "
        QgsMessageLog.logMessage(
            error_message,
            level=Qgis.Critical,
        )
        iface.messageBar().pushMessage(
            "Erreur",
            error_message,
            level=Qgis.Critical,
        )
        return

    layer.loadNamedStyle(str(qml_file_path))

    # getting statistics from the layer
    stats: QgsRasterBandStats = layer.dataProvider().bandStatistics(
        1, QgsRasterBandStats.All, layer.extent()
    )
    min_raster_value: float = stats.minimumValue
    max_raster_value: float = stats.maximumValue

    # # adjusting the symbology to equal intervals from the
    renderer: QgsSingleBandPseudoColorRenderer = layer.renderer()

    shader: QgsRasterShader = renderer.shader()

    color_ramp_shader = shader.rasterShaderFunction()

    if isinstance(color_ramp_shader, QgsColorRampShader):
        current_color_ramp_item_list = color_ramp_shader.colorRampItemList()
        classes_count: int = len(current_color_ramp_item_list)
        new_color_ramp_list = []

        for i in range(0, classes_count):
            val = min_raster_value + (
                i * (max_raster_value - min_raster_value) / (classes_count - 1)
            )
            item = QgsColorRampShader.ColorRampItem(
                val, (current_color_ramp_item_list[i]).color, str(val)
            )
            new_color_ramp_list.append(item)
        color_ramp_shader.setColorRampItemList(new_color_ramp_list)


def get_unique_raster_values_as_int(raster_file_path: str) -> list[int]:
    """
    Extract values from a raster layer and return a list of values as integers.

    Args:
        raster_file_path (str): The file path of the raster layer.

    Returns:
        list[int]: A list of values from the raster layer as integers.
    """
    dataset = gdal.Open(raster_file_path)  # DataSet
    if dataset is None:
        return []

    band = dataset.GetRasterBand(1)  # -> band
    array = np.array(band.ReadAsArray())  # -> matrice values
    values = np.unique(array)

    return [int(floor(x)) for x in values]


def get_raster_nodata_value(raster_file_path: str) -> Union[int, None]:
    """
    Extract the nodata value from a raster layer and return it as an integer.

    Args:
        raster_file_path (str): The file path of the raster layer.

    Returns:
        Union[int,None]: The nodata value as an integer or None if the raster layer has no nodata value.
    """
    dataset = gdal.Open(raster_file_path)  # DataSet
    if dataset is None:
        return None

    band = dataset.GetRasterBand(1)  # -> band
    nodata = band.GetNoDataValue()

    return int(floor(nodata)) if nodata is not None else None


@dataclass
class RasterLoadConfig:
    """Configuration for loading rasters from a directory to the QGIS instance."""

    raster_directory: Path
    group_name: str = "group"
    raster_file_extensions: list[str] = field(
        default_factory=lambda: CHLOE_RASTER_FILE_EXTENSIONS
    )
    group_is_expanded: bool = False
    group_is_checked: bool = False
    qml_file_path: Path = Path()


def load_rasters_from_directory_to_qgis_instance(config: RasterLoadConfig) -> None:
    """load rasters from a given directory to the QGIS instance."""
    qgs_project = QgsProject.instance()
    layer_tree = qgs_project.layerTreeRoot()

    # add main group
    root_group: QgsLayerTreeGroup = layer_tree.addGroup(config.group_name)
    root_group.setExpanded(config.group_is_expanded)
    root_group.setItemVisibilityChecked(config.group_is_checked)

    for filename in config.raster_directory.iterdir():
        if filename.suffix in config.raster_file_extensions:
            raster_layer: QgsRasterLayer = QgsRasterLayer(str(filename), filename.stem)
            if not raster_layer.isValid():
                iface.messageBar().pushMessage(
                    "Erreur",
                    f"Impossible de charger le raster {filename}",
                    level=Qgis.Critical,
                )
            set_raster_layer_symbology(
                layer=raster_layer, qml_file_path=config.qml_file_path
            )
            qgs_project.addMapLayer(raster_layer, False)
            root_group.addLayer(raster_layer)


def convert_int_to_odd(input_integer: int) -> int:
    """
    Returns an odd number if the input number is even.

    Parameters:
    input_integer (int): The integer to be converted to an odd number.

    Returns:
    int: The converted odd number.
    """
    if int(input_integer) % 2 == 0:
        return int(input_integer) + 1
    else:
        return int(input_integer)


def get_layer_name(
    layer: Union[str, QgsRasterLayer], default_output: str = "output"
) -> str:
    """
    Get the name of a QgsRasterLayer or a file path string.

    Args:
        layer (Union[str, QgsRasterLayer]): A QgsRasterLayer object or a file path string.
        default_output (str, optional): The default output name if layer is None. Defaults to "output".

    Returns:
        str: The name of the layer or file path without the extension.

    """
    res: str = default_output
    if layer is None:
        return res
    if isinstance(layer, QgsRasterLayer):
        layer_source = layer.dataProvider().dataSourceUri()
        res = str(Path(layer_source).stem)
    elif isinstance(layer, str):
        res = str(Path(layer).stem)
    else:
        res = str(layer)
    return res
