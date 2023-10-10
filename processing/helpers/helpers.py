from enum import Enum
from typing import Union

from jinja2 import Template
from ..algorithms.helpers.constants_metrics import (
    FAST_MODE_EXCLUSION_METRICS,
    TYPES_OF_METRICS_SIMPLE,
    TYPES_OF_METRICS_CROSS,
    TYPES_OF_METRICS,
)


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


def enum_to_list(
    enum_class: Enum, return_enum_names: bool = False
) -> list[Union[str, int, float]]:
    """
    Convert an Enum class to a list of its values or names.

    Args:
        enum_class (Enum): The Enum class to convert.
        return_enum_names (bool, optional): Whether to return the names of the Enum elements instead of their values. Defaults to False.

    Returns:
        list[Union[str, int, float]]: A list of the Enum elements' values or names.
    """
    if return_enum_names:
        return [element.name for element in enum_class]
    else:
        return [element.value for element in enum_class]


def get_enum_element_index(enum_element: Enum) -> int:
    """
    Returns the index of an Enum element within its class.

    Parameters:
    enum_element (Enum): The Enum element to get the index of.

    Returns:
    int: The index of the Enum element within its class.
    """

    enum_class = type(enum_element)
    enum_dict = enum_to_dict(enum_class)
    return list(enum_dict.keys()).index(enum_element.name)
