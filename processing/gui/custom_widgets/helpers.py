from csv import reader
from pathlib import Path
from typing import Any, Union
from re import Pattern, match
from qgis.core import QgsRasterLayer, QgsProject, QgsMessageLog, Qgis
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QAbstractItemModel, QVariant

from processing.gui.wrappers import WidgetWrapper
from processing.gui.BatchPanel import BatchPanel
from processing.gui.wrappers import (
    DIALOG_MODELER,
    DIALOG_BATCH,
)

from ....helpers.helpers import tr
from ..chloe_algorithm_dialog import ChloeParametersPanel

# TODO : Add translation to messages


def get_param_wrappers_from_algorithm_dialog(
    algorithm_dialog, dialog_type: str
) -> dict[str, QgsAbstractProcessingParameterWidgetWrapper]:
    """Get the parameter wrappers from the algorithm dialog"""
    if dialog_type == DIALOG_BATCH:
        return algorithm_dialog.mainWidget().wrappers[0]
    elif dialog_type == DIALOG_MODELER:
        return algorithm_dialog.widget.widget.wrappers
    else:
        return algorithm_dialog.mainWidget().wrappers


def get_widget_wrapper_from_param_name(
    wrappers: list[QgsAbstractProcessingParameterWidgetWrapper], param_name: str
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


def get_parameter_widget_wrapper_from_batch_panel(
    batch_panel: BatchPanel, parameter_name: str
) -> Union[WidgetWrapper, None]:
    """Get a widget wrapper of a parameter from the processign batch panel"""

    for wrapper in batch_panel.wrappers[0]:
        if (
            wrapper is not None
            and wrapper.parameterDefinition().name() == parameter_name
        ):
            return wrapper
    return None


def get_parameter_value_from_batch_panel(
    batch_panel: BatchPanel, parameter_name: str
) -> Union[str, None]:
    """Get the input raster layer parameter from the processign batch panel"""

    for wrapper in batch_panel.wrappers[0]:
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


def get_parameter_value_from_panel(
    dialog_type: str,
    param_name: str,
    parameters_panel: Union[BatchPanel, ChloeParametersPanel],
) -> Union[str, None]:
    """Get the input raster layer parameter"""

    if dialog_type == DIALOG_BATCH:
        value = get_parameter_value_from_batch_panel(
            batch_panel=parameters_panel, parameter_name=param_name
        )
    else:
        widget = parameters_panel.wrappers[param_name]
        value: Union[str, QVariant, None] = None
        try:
            value = widget.value()
        except AttributeError:
            # used if the widget is a QgsAbstractProcessingParameterWidgetWrapper
            value = widget.widgetValue()

        # empty param returns a NULL QVariant if empty

    return None if (isinstance(value, QVariant) and value.isNull()) else value


def get_parameter_value_from_batch_standard_algorithm_dialog(
    dialog_type: str, param_name: str, algorithm_dialog
) -> Union[Any, None]:
    """Get the value of a given parameter name in the algorithm dialog"""
    # TODO : implement for modeler dialog
    if dialog_type == DIALOG_MODELER:
        return ""

    parameters_panel: Union[
        BatchPanel, ChloeParametersPanel
    ] = algorithm_dialog.mainWidget()

    if not parameters_panel:
        return ""

    return get_parameter_value_from_panel(
        dialog_type=dialog_type,
        param_name=param_name,
        parameters_panel=parameters_panel,
    )


def replace_param_widget_value(
    algorithm_dialog, dialog_type: str, param_name: str, value: Any
):
    """Replaces the value of a parameter widget with the given value.

    Args:
        param_name (str): The name of the parameter to replace the value of.
        value (Any): The new value to set for the parameter widget.

    Returns:
        None
    """
    wrappers = get_param_wrappers_from_algorithm_dialog(
        algorithm_dialog=algorithm_dialog, dialog_type=dialog_type
    )

    param_widget = wrappers[param_name]
    if param_widget is None:
        QgsMessageLog.logMessage(
            f"{tr('Could not find widget for parameter')} {param_name}",
            level=Qgis.Critical,
        )
    else:
        try:
            param_widget.setParameterValue(value, algorithm_dialog.processingContext())
        except AttributeError:
            # log
            QgsMessageLog.logMessage(
                f"{tr('Could not set parameter value for parameter')} {param_name}",
                level=Qgis.Critical,
            )


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
        return (
            selected_layer.dataProvider().dataSourceUri()
            if selected_layer is not None
            else ""
        )
    else:
        return input_raster_layer_param_value


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


def csv_file_has_min_column_count(
    csv_file_path: Path, minimum_column_count: int
) -> bool:
    """Check if the csv file has at least the given minimum column count."""
    try:
        with open(str(csv_file_path), "r", encoding="utf-8") as csv_file:
            csv_reader = reader(csv_file, delimiter=";")
            header = next(csv_reader)
            return len(header) >= minimum_column_count
    except FileNotFoundError:
        QMessageBox.critical(
            None, "Error", f"{str(csv_file_path)} {tr('does not exist')}"
        )
        return False
    except PermissionError:
        QMessageBox.critical(
            None,
            "Error",
            f"{str(csv_file_path)} {tr('is not accessible. Please check the file permissions.')}",
        )
        return False
    except UnicodeDecodeError:
        QMessageBox.critical(
            None,
            "Error",
            f"{str(csv_file_path)} {tr('is not a valid csv file. Please check the file encoding.')}",
        )
        return False


def csv_file_column_is_type_integer(
    csv_file_path: Path, column_idx_to_check: int = 0
) -> bool:
    """Check if the csv file column has integer values."""
    try:
        with open(str(csv_file_path), "r", encoding="utf-8") as csv_file:
            csv_reader = reader(csv_file, delimiter=";")
            next(csv_reader)
            for row in csv_reader:
                try:
                    int(row[column_idx_to_check])
                except ValueError:
                    return False
            return True
    except FileNotFoundError:
        QMessageBox.critical(
            None, "Error", f"{str(csv_file_path)} {tr('does not exist')}"
        )
        return False
    except PermissionError:
        QMessageBox.critical(
            None,
            "Error",
            f"{str(csv_file_path)} {tr('is not accessible. Please check the file permissions.')}",
        )
        return False
    except UnicodeDecodeError:
        QMessageBox.critical(
            None,
            "Error",
            f"{str(csv_file_path)} {tr('is not a valid csv file. Please check the file encoding.')}",
        )
        return False


def csv_file_has_duplicates(csv_file_path: Path, column_idx_to_check: int = 0) -> bool:
    """Check if the csv file has duplicates values"""
    try:
        with open(str(csv_file_path), "r", encoding="utf-8") as csv_file:
            csv_reader = reader(csv_file, delimiter=";")
            next(csv_reader)
            values = []
            duplicates: list[str] = []
            for row in csv_reader:
                value = row[column_idx_to_check]
                if value in values:
                    duplicates.append(value)
                else:
                    values.append(value)
            if duplicates:
                QMessageBox.critical(
                    None,
                    "Error",
                    f"{tr('Duplicated values in column')} {column_idx_to_check} ({', '.join(duplicates)})",
                )
                return True
            return False
    except FileNotFoundError:
        QMessageBox.critical(
            None, "Error", f"{str(csv_file_path)} {tr('does not exist')}"
        )
        return False
    except PermissionError:
        QMessageBox.critical(
            None,
            "Error",
            f"{str(csv_file_path)} {tr('is not accessible. Please check the file permissions.')}",
        )
        return False
    except UnicodeDecodeError:
        QMessageBox.critical(
            None,
            "Error",
            f"{str(csv_file_path)} {tr('is not a valid csv file. Please check the file encoding.')}",
        )
        return False


def get_csv_file_headers_list(
    csv_file_path: Path, skip_columns_indexes: list[int]
) -> list[str]:
    """Get the csv file headers list."""
    try:
        with open(str(csv_file_path), "r", encoding="utf-8") as csv_file:
            csv_reader = reader(csv_file, delimiter=";")
            headers = next(csv_reader)
            headers_list: list[str] = []
            # skip columns if their index are in the skip_columns_indexes list
            for idx, header in enumerate(headers):
                if idx not in skip_columns_indexes:
                    headers_list.append(header)
            return headers_list
    except FileNotFoundError:
        QMessageBox.critical(
            None, "Error", f"{str(csv_file_path)} {tr('does not exist')}"
        )
        return []
    except PermissionError:
        QMessageBox.critical(
            None,
            "Error",
            f"{str(csv_file_path)} {tr('is not accessible. Please check the file permissions.')}",
        )
        return []
    except UnicodeDecodeError:
        QMessageBox.critical(
            None,
            "Error",
            f"{str(csv_file_path)} {tr('is not a valid csv file. Please check the file encoding.')}",
        )
        return []


def get_filtered_csv_headers_list(
    csv_file_path: Path, skip_header_names_pattern: Pattern
) -> list[str]:
    """
    Get the csv file headers list, skipping headers whose names match the given pattern.

    Args:
        csv_file_path (Path): The path to the csv file.
        skip_header_names_pattern (Pattern): The pattern to match against header names.

    Returns:
        list[str]: The list of csv file headers, with skipped headers removed.

    Raises:
        FileNotFoundError: If the csv file does not exist.
        PermissionError: If the csv file is not accessible due to file permissions.
        UnicodeDecodeError: If the csv file is not a valid csv file due to encoding issues.
    """
    try:
        with open(str(csv_file_path), "r", encoding="utf-8") as csv_file:
            csv_reader = reader(csv_file, delimiter=";")
            headers = next(csv_reader)
            headers_list: list[str] = []
            # skip columns if their names matches the skip_columns_names_pattern
            for header in headers:
                if skip_header_names_pattern.match(header):
                    continue
                headers_list.append(header)
            return headers_list
    except FileNotFoundError:
        QMessageBox.critical(
            None, "Error", f"{str(csv_file_path)} {tr('does not exist')}"
        )
        return []
    except PermissionError:
        QMessageBox.critical(
            None,
            "Error",
            f"{str(csv_file_path)} {tr('is not accessible. Please check the file permissions.')}",
        )
        return []
    except UnicodeDecodeError:
        QMessageBox.critical(
            None,
            "Error",
            f"{str(csv_file_path)} {tr('is not a valid csv file. Please check the file encoding.')}",
        )
        return []


def csv_file_path_is_valid(csv_file: Path) -> bool:
    """Check if the csv map file is valid"""
    if csv_file is None or csv_file == Path():
        QMessageBox.critical(
            None,
            tr("Csv file error"),
            tr("No csv file selected. Please select a csv file first."),
        )
        return False
    if not csv_file.exists():
        QMessageBox.critical(
            None,
            tr("Csv file error"),
            f"{csv_file} {tr('does not exist')}",
        )
        return False
    return True


def value_exists_in_model_column(
    model: QAbstractItemModel,
    value: str,
    column_index: int = 0,
    skip_row_index: int = -1,
) -> bool:
    """ "
    Checks if a value exists in a given column of a QAbstractItemModel model.

    Args:
        model (QAbstractItemModel): The model to check.
        value (str): The value to check.
        column_index (int, optional): The index of the column to check. Defaults to 0.
        skip_row_index (int, optional): The index of the row to skip. Defaults to -1.

    Returns:
        bool: True if the value exists, False otherwise.
    """
    for row in range(model.rowCount()):
        if row == skip_row_index:
            continue
        item = model.item(row, column_index)
        if item is not None and item.text() != "":
            if value == item.text():
                return True
    return False
