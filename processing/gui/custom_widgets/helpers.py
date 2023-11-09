from typing import Union
from re import match
from qgis.core import QgsRasterLayer, QgsProject
from processing.gui.wrappers import WidgetWrapper
from processing.gui.BatchPanel import BatchPanel
from processing.gui.wrappers import (
    DIALOG_MODELER,
    DIALOG_BATCH,
)
from ..chloe_algorithm_dialog import ChloeParametersPanel


def get_widget_wrapper_from_param_name(
    wrappers, param_name: str
) -> Union[WidgetWrapper, None]:
    """Returns the WidgetWrapper object from a list of wrappers that matches the given parameter name.

    Args:
        wrappers (list): A list of WidgetWrapper objects.
        param_name (str): The name of the parameter to match.

    Returns:
        WidgetWrapper: The WidgetWrapper object that matches the given parameter name.
    """
    for wrapper in wrappers:
        if wrapper.parameterDefinition().name() == param_name:
            return wrapper
    return None


def extract_raster_layer_path(input_raster_layer_param_value: Union[str, None]) -> str:
    """
    Extracts the raster layer path based on the parameter value.

    Args:
        input_raster_layer_param_value (Union[str, None]): The input raster layer parameter value.

    Returns:
        str: The raster layer path.
    """
    if input_raster_layer_param_value is None:
        return ""

    # if the given input_raster_layer is a qgs map layer id
    if match(r"^[a-zA-Z0-9_]+$", input_raster_layer_param_value):
        selected_layer: QgsRasterLayer = QgsProject.instance().mapLayer(
            input_raster_layer_param_value
        )
        return selected_layer.dataProvider().dataSourceUri()
    else:
        return input_raster_layer_param_value


def get_parameter_value_from_batch_panel(
    widget: BatchPanel, parameter_name: str
) -> Union[str, None]:
    """Get the input raster layer parameter from the processign batch panel"""

    for wrapper in widget.wrappers[0]:
        if (
            wrapper is not None
            and wrapper.parameterDefinition().name() == parameter_name
        ):
            try:
                value = wrapper.value()
            except AttributeError:
                # used if the widget is a QgsAbstractProcessingParameterWidgetWrapper
                value = wrapper.widgetValue()
            return value
    return None


def get_parameter_widget_from_batch_panel(
    widget: BatchPanel, parameter_name: str
) -> Union[WidgetWrapper, None]:
    """Get a widget wrapper of a parameter from the processign batch panel"""

    for wrapper in widget.wrappers[0]:
        if (
            wrapper is not None
            and wrapper.parameterDefinition().name() == parameter_name
        ):
            return wrapper
    return None


def get_parameter_value_from_panel(
    dialog_type: str,
    param_name: str,
    widget: Union[BatchPanel, ChloeParametersPanel],
) -> Union[str, None]:
    """Get the input raster layer parameter"""

    if dialog_type == DIALOG_BATCH:
        value = get_parameter_value_from_batch_panel(
            widget=widget, parameter_name=param_name
        )
    else:
        widget = widget.wrappers[param_name]
        value: Union[str, QVariant, None] = None
        try:
            value = widget.value()
        except AttributeError:
            # used if the widget is a QgsAbstractProcessingParameterWidgetWrapper
            value = widget.widgetValue()

        # empty param returns a NULL QVariant if empty

    return None if (isinstance(value, QVariant) and value.isNull()) else value


def get_parameter_value_from_algorithm_dialog(
    dialog_type: str, param_name: str, algorithm_dialog
) -> Union[Any, None]:
    """Get the value of a given parameter name in the algorithm dialog"""
    # TODO : implement for modeler dialog
    if dialog_type == DIALOG_MODELER:
        return ""

    widget: Union[BatchPanel, ChloeParametersPanel] = algorithm_dialog.mainWidget()

    if not widget:
        return ""

    return get_parameter_value_from_panel(
        dialog_type=dialog_type, param_name=param_name, widget=widget
    )


def get_input_raster_param_path(
    dialog_type: str, input_raster_layer_param_name: str, algorithm_dialog
) -> str:
    """Get the input raster layer path"""

    if dialog_type == DIALOG_MODELER:
        return ""

    widget: Union[BatchPanel, ChloeParametersPanel] = algorithm_dialog.mainWidget()

    if not widget:
        return ""

    input_raster_layer_param_value = get_parameter_value_from_panel(
        dialog_type, input_raster_layer_param_name, widget
    )

    if input_raster_layer_param_value is None:
        return ""

    return extract_raster_layer_path(input_raster_layer_param_value)
