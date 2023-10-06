from enum import Enum

from pathlib import Path
from typing import Union
import numpy as np
from math import floor
from osgeo import gdal
from qgis.core import (
    QgsRasterLayer,
    QgsRasterBandStats,
    QgsMessageLog,
    Qgis,
)

from jinja2 import Template
from ..algorithms.helpers.constants_metrics import (
    FAST_MODE_EXCLUSION_METRICS,
    TYPES_OF_METRICS_SIMPLE,
    TYPES_OF_METRICS_CROSS,
    TYPES_OF_METRICS,
)


def set_raster_layer_symbology(layer: QgsRasterLayer, qml_file_name: str) -> None:
    """Set the layer symbology from a qml file."""

    style_file_path: Path = (
        Path(__file__).resolve().parent.parent / "styles" / qml_file_name
    )

    if not layer.isValid():
        QgsMessageLog.logMessage(
            f"Fichier raster non valide : {layer.source()} ",
            level=Qgis.Critical,
        )
        return
    print(str(style_file_path))
    layer.loadNamedStyle(str(style_file_path))

    # getting statistics from the layer
    stats: QgsRasterBandStats = layer.dataProvider().bandStatistics(
        1, QgsRasterBandStats.All, layer.extent()
    )
    min: float = stats.minimumValue
    max: float = stats.maximumValue

    # # adjusting the symbology to equal intervals from the
    # renderer = layer.renderer()
    # shader = renderer.shader()
    # colorRampShader = shader.rasterShaderFunction()
    # if type(colorRampShader) is QgsColorRampShader:
    #     colorRampItemList = colorRampShader.colorRampItemList()
    #     nbClasses = len(colorRampItemList)
    #     newColorRampList = []
    #     for i in range(0, nbClasses):
    #         val = min + (i * (max - min) / (nbClasses - 1))
    #         item = QgsColorRampShader.ColorRampItem(
    #             val, (colorRampItemList[i]).color, str(val)
    #         )
    #         newColorRampList.append(item)
    #     colorRampShader.setColorRampItemList(newColorRampList)


def extract_non_zero_non_nodata_values(raster_file_path: str) -> list[int]:
    """Extract values from a raster layer and return a list of values as integers, removing 0 and nodata values"""
    dataset = gdal.Open(raster_file_path)  # DataSet
    if dataset is None:
        QgsMessageLog.logMessage(
            f"Le fichier raster {raster_file_path} n'est pas valide",
            level=Qgis.Critical,
        )
        return []

    band = dataset.GetRasterBand(1)  # -> band
    array = np.array(band.ReadAsArray())  # -> matrice values
    values = np.unique(array)
    nodata = band.GetNoDataValue()

    int_values_and_nodata: list[int] = [
        int(floor(x)) for x in values[(values != 0) & (values != nodata)]
    ]

    return int_values_and_nodata


def add_simple_metrics(
    metrics: dict[str, list[str]], raster_values: list[int]
) -> dict[str, list[str]]:
    """Add simple metrics to the metrics dictionnary based on the raster values"""
    raster_values.sort()
    # Remove duplicates to get a clean array
    unique_raster_values: set[int] = set(raster_values)
    no_zero_raster_values: list[int] = [val for val in unique_raster_values if val != 0]

    if len(no_zero_raster_values) < 1000:
        for simple_metric_name, simple_metric_list in TYPES_OF_METRICS_SIMPLE.items():
            metrics[simple_metric_name].extend(
                [
                    metric + str(val)
                    for metric in simple_metric_list
                    for val in no_zero_raster_values
                ]
            )

    return metrics


def add_cross_metrics(
    metrics: dict[str, list[str]], raster_values: list[int]
) -> dict[str, list[str]]:
    """Add cross metrics to the metrics dictionnary based on the raster values"""
    raster_values.sort()
    # Remove duplicates to get a clean array
    unique_raster_values: set[int] = set(raster_values)
    no_zero_raster_values: list[int] = [val for val in unique_raster_values if val != 0]

    if len(no_zero_raster_values) < 100:
        for cross_metric_name, cross_metrics_list in TYPES_OF_METRICS_CROSS.items():
            metrics[cross_metric_name].extend(
                [
                    mc + str(val1) + "-" + str(val2)
                    for mc in cross_metrics_list
                    for val1 in no_zero_raster_values
                    for val2 in no_zero_raster_values
                    if val1 <= val2
                ]
            )

    return metrics


def remove_metrics(
    input_metrics_dict: dict[str, list[str]], metrics_to_remove: list[str]
) -> dict[str, list[str]]:
    """Remove metrics from the metrics dictionnary"""
    result_metrics_dict = {
        metric_name: metric_list
        for metric_name, metric_list in input_metrics_dict.items()
        if metric_name not in metrics_to_remove
    }

    return result_metrics_dict


def get_metrics(
    raster_values: list[int], fast_mode: bool = False
) -> dict[str, list[str]]:
    """Get the metric dictionnary based on the raster values"""
    metrics: dict[str, list[str]] = TYPES_OF_METRICS

    metrics = add_simple_metrics(metrics, raster_values)
    metrics = add_cross_metrics(metrics, raster_values)
    if fast_mode:
        metrics = remove_metrics(metrics, FAST_MODE_EXCLUSION_METRICS)
    return metrics


def format_path_for_properties_file(input_string: str, is_windows_system: bool = False):
    """Format path file for windows"""
    # TODO : check if it is necessary ??
    if is_windows_system:
        return input_string.replace("/", "\\").replace("\\", "\\\\").replace(":", "\:")
    return input_string


def convert_to_odd(input_integer: int) -> int:
    """returns a odd number if input number is even"""
    if int(input_integer) % 2 == 0:
        return int(input_integer) + 1
    else:
        return int(input_integer)


def get_layer_name(layer, default_output: str = "output") -> str:
    """Get layer name from QgsRasterLayer or str"""
    res: str = default_output
    if layer is None:
        return res
    if not (layer is None):
        if isinstance(layer, QgsRasterLayer):
            layer_source = layer.dataProvider().dataSourceUri()
            res = str(Path(layer_source).stem)
        elif isinstance(layer, str):
            res = str(Path(layer).stem)
        else:
            res = str(layer)
    return res


def file_get_content(filename, encoding="utf-8", context=None) -> str:
    """Get file content and return it as a string"""
    try:
        with open(filename, "r", encoding=encoding) as file:
            data = file.read()
            if context is not None:
                template = Template(data)
                return template.render(context)
            else:
                return data
    except FileNotFoundError:
        return ""


def enum_to_dict(
    enum_class: Enum, values_only: bool = False
) -> dict[str, Union[int, str]]:
    """
    Converts an enum class to a dictionary where enum names are keys and enum values are values.

    Args:
        enum_class (Enum): The enum class to convert.

    Returns:
        dict: A dictionary with enum names as keys and enum values as values.
    """
    enum_dict = {}
    for enum_member in enum_class:
        if values_only:
            enum_dict[enum_member.value] = enum_member.value
        else:
            enum_dict[enum_member.name] = enum_member.value

    return enum_dict


def enum_to_list(enum_class: Enum) -> list[Union[str, int, float]]:
    """convert enum class to list"""
    return [element.value for element in enum_class]


def get_enum_order_as_int(enum_element: Enum) -> int:
    """
    Returns the order number of an element in an enum class.

    Args:
        enum_element (Enum): The enum element to search for.

    Returns:
        int: The order number of the element in the enum class.
    """
    enum_class = type(enum_element)
    enum_dict = enum_to_dict(enum_class)
    return list(enum_dict.keys()).index(enum_element.name)
