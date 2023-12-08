from pathlib import Path
from typing import Any, Protocol, Union
from re import Pattern, match
from .....helpers.helpers import (
    get_raster_nodata_value,
    get_unique_raster_values,
)
from ...custom_widgets.helpers import (
    csv_file_path_is_valid,
    get_csv_file_headers_list,
    get_filtered_csv_headers_list,
    get_input_raster_param_path,
    get_parameter_value_from_batch_standard_algorithm_dialog,
)


class ValueSelectorStrategy(Protocol):
    """Strategy abstract class for getting the values for the value selector panel"""

    def get_data(self) -> list[str]:
        ...

    def convert_selected_values_to_properties_file_element(
        self, selected_values: list[str]
    ) -> str:
        ...

    def get_current_selected_values_from_line_edit(
        self, line_edit_text: str
    ) -> list[str]:
        ...


RASTER_NO_DATA_VALUE_INDICATOR: str = "(No data)"


class RasterValueSelectorStrategy:
    """
    A value selector strategy for getting the values from a raster.

    Attributes:
        input_raster_name (str): The name of the input raster.
        dialog_type (str): The type of dialog.
        algorithm_dialog: The algorithm dialog.
    """

    def __init__(
        self, input_raster_name: str, dialog_type: str, algorithm_dialog
    ) -> None:
        self.input_raster_name: str = input_raster_name
        self.dialog_type: str = dialog_type
        self.algorithm_dialog = algorithm_dialog

    def get_raster_input_path(self) -> str:
        """
        Get the path to the raster input.

        Returns:
            str: The path to the raster input.
        """
        return get_input_raster_param_path(
            dialog_type=self.dialog_type,
            input_raster_layer_param_name=self.input_raster_name,
            algorithm_dialog=self.algorithm_dialog,
        )

    def get_data(self) -> list[str]:
        """
        Get the data from the raster.
        Returns:
            list[str]: A list of strings representing the raster data.
        """
        raster_data_list: list[str] = []

        raster_file_path: str = self.get_raster_input_path()

        if not raster_file_path:
            return raster_data_list

        raster_values: list[float] = get_unique_raster_values(
            raster_file_path=raster_file_path, as_int=True
        )
        nodata_value: Union[float, None] = get_raster_nodata_value(
            raster_file_path=raster_file_path
        )

        if nodata_value is not None:
            raster_data_list.append(
                f"{str(int(nodata_value))} {RASTER_NO_DATA_VALUE_INDICATOR}"
            )

        raster_data_list.extend([str(int(value)) for value in raster_values])
        return raster_data_list

    def convert_selected_values_to_properties_file_element(
        self, selected_values: list[str]
    ) -> str:
        """
        Convert the selected values to a string, replacing any instances of the no data value with the actual no data value.
        Args:
            selected_values (list[str]): The list of selected value in the diallist

        Returns: A string formatted for the properties file.
        """
        digit_values: list[str] = []
        for value in selected_values:
            if RASTER_NO_DATA_VALUE_INDICATOR in value:
                digit_match = match(r"^-?\d+", value)
                if digit_match:
                    digit_values.append(digit_match.group())
            else:
                digit_values.append(value)

        return ";".join(digit_values)

    def get_current_selected_values_from_line_edit(
        self, line_edit_text: str
    ) -> list[str]:
        """
        Get the current selected values from the value selector panel qline edit text

        Returns:
            list[str]: A list of the current selected values.
        """
        current_values: list[str] = []

        if not line_edit_text:
            return current_values

        raster_file_path: str = self.get_raster_input_path()

        nodata_value: Union[float, None] = get_raster_nodata_value(
            raster_file_path=raster_file_path
        )

        for value in line_edit_text.split(";"):
            if nodata_value is not None and value == str(int(nodata_value)):
                current_values.append(
                    f"{str(nodata_value)} {RASTER_NO_DATA_VALUE_INDICATOR}"
                )
            else:
                current_values.append(value)

        return current_values


class CSVHeaderValueSelectorStrategy:
    """
    A value selector strategy for getting the values of headers csv.

    Attributes:
        input_csv_name (str): The name of the input csv file.
        dialog_type (str): The type of dialog.
        algorithm_dialog: The algorithm dialog.
    """

    def __init__(self, input_csv_name: str, dialog_type: str, algorithm_dialog) -> None:
        self.input_csv_name: str = input_csv_name
        self.dialog_type: str = dialog_type
        self.algorithm_dialog = algorithm_dialog
        self.skip_header_names_pattern: Union[Pattern, None] = None

    def set_skip_header_names_pattern(self, pattern: Pattern) -> None:
        """
        Set the pattern for skipping header names.

        Args:
            pattern: The pattern for skipping header names.
        """
        self.skip_header_names_pattern = pattern

    def get_csv_input_path(self) -> str:
        """
        Returns the path of the CSV file selected by the user in the algorithm dialog.

        Returns:
            str: The path of the selected CSV file, or an empty string if no file was selected.
        """
        csv_file: Union[
            Any, None
        ] = get_parameter_value_from_batch_standard_algorithm_dialog(
            dialog_type=self.dialog_type,
            param_name=self.input_csv_name,
            algorithm_dialog=self.algorithm_dialog,
        )

        if csv_file is None:
            return ""

        return csv_file

    def get_data(self) -> list[str]:
        """
        Returns a list of headers from a CSV file, excluding the first two columns (should be X and Y).

        Returns:
            A list of strings representing the headers from the CSV file.
        """
        csv_file_path: Path = Path(self.get_csv_input_path())
        if not csv_file_path_is_valid(csv_file=csv_file_path):
            return []

        # Get the headers from the csv file and skip the two first columns
        if self.skip_header_names_pattern is not None:
            csv_headers: list[str] = get_filtered_csv_headers_list(
                csv_file_path=csv_file_path,
                skip_header_names_pattern=self.skip_header_names_pattern,
            )
        else:
            csv_headers = get_csv_file_headers_list(
                csv_file_path, skip_columns_indexes=[]
            )

        return csv_headers

    def convert_selected_values_to_properties_file_element(
        self, selected_values: list[str]
    ) -> str:
        """
        Converts a list of selected values to a string that can be used as an element in a properties file.

        Args:
            selected_values: A list of selected values.

        Returns:
            A string that can be used as an element in a properties file.
        """
        return ";".join(selected_values)

    def get_current_selected_values_from_line_edit(
        self, line_edit_text: str
    ) -> list[str]:
        """
        Get the current selected values from the value selector panel qline edit text

        Returns:
            list[str]: A list of the current selected values.
        """
        current_values: list[str] = []

        if not line_edit_text:
            return current_values

        for value in line_edit_text.split(";"):
            current_values.append(value)

        return current_values
