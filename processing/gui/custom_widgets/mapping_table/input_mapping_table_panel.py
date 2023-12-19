from typing import Any, Union
from pathlib import Path
from csv import reader
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QMessageBox, QHeaderView

from processing.gui.wrappers import DIALOG_STANDARD
from ....algorithms.helpers.constants import MAP_CSV
from .....helpers.helpers import get_raster_nodata_value, get_unique_raster_values, tr
from ..helpers import (
    csv_file_column_is_type_integer,
    csv_file_has_duplicates,
    csv_file_has_min_column_count,
    get_csv_file_headers_list,
    get_input_raster_param_path,
    get_parameter_value_from_batch_standard_algorithm_dialog,
)

from .models import MappingModelIntValueDelegate, MappingTableModel

WIDGET, BASE = uic.loadUiType(
    Path(__file__).resolve().parent / "DlgMappingTableInput.ui"
)


class TableMappingPanel(BASE, WIDGET):
    """Table widget to map input values to output values"""

    def __init__(
        self,
        parent,
        input_raster_layer_param_name: str = "",
        dialog_type: str = DIALOG_STANDARD,
    ):
        super().__init__()
        self.setupUi(self)
        self.dialog = parent
        self.dialog_type: str = dialog_type
        self.input_raster_layer_param_name: str = input_raster_layer_param_name
        self._table_model: MappingTableModel = MappingTableModel()

        self.button_read_values_from_input.clicked.connect(
            self.populate_mapping_table_from_raster_input
        )
        self.button_populate_from_csv.clicked.connect(
            self.populate_mapping_table_from_csv
        )

        self.pushButton_add_tableview_row.clicked.connect(self.add_table_row)
        self.pushButton_delete_tableview_row.clicked.connect(self.remove_table_row)

        self._table_model.signal_model_updated.connect(self.update_propertie_value)

        self.init_gui()

    def init_gui(self) -> None:
        self.tableView_mapping.setModel(self._table_model)
        self.tableView_mapping.setItemDelegateForColumn(
            0, MappingModelIntValueDelegate(self.tableView_mapping)
        )
        #  Set columns to stretch to the remaining space
        self.tableView_mapping.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

    def add_table_row(self) -> None:
        """Add a row to the mapping table"""
        self._table_model.appendRow([None, None])

    def remove_table_row(self) -> None:
        """Remove a row from the mapping table"""
        self._table_model.removeRow(self.tableView_mapping.currentIndex().row())

    def populate_mapping_table_from_raster_input(self) -> None:
        """
        Populates the mapping table with values from the input raster layer.

        Extracts non-zero and non-nodata values from the input raster layer and sets them as data in the table model.
        """
        raster_file_path: str = get_input_raster_param_path(
            dialog_type=self.dialog_type,
            input_raster_layer_param_name=self.input_raster_layer_param_name,
            algorithm_dialog=self.dialog,
        )
        # get raster values
        raster_int_values: list[float] = get_unique_raster_values(
            raster_file_path=raster_file_path, as_int=True
        )

        nodata_value: Union[float, None] = get_raster_nodata_value(
            raster_file_path=raster_file_path
        )

        raster_data_list: list[int] = []

        if nodata_value is not None:
            raster_data_list.append(int(nodata_value))

        raster_data_list.extend([int(raster) for raster in raster_int_values])

        self._table_model.set_data(
            set((str(raster_value), "") for raster_value in raster_data_list)
        )

    def clear_mapping_table(self) -> None:
        """Clear the mapping table"""
        self._table_model.clear_data()

    def clear_csv_header_combobox(self) -> None:
        """Clear the csv header combobox"""
        self.combobox_csv_headers_selector.clear()

    def get_csv_file_from_widget(self) -> str:
        """Get the CSV file path from the input widget in the dialog.

        Returns:
            str: The path to the CSV file, or an empty string if no file was selected.
        """

        csv_file: Union[
            Any, None
        ] = get_parameter_value_from_batch_standard_algorithm_dialog(
            dialog_type=self.dialog_type,
            param_name=MAP_CSV,
            algorithm_dialog=self.dialog,
        )

        if csv_file is None:
            return ""

        return str(csv_file)

    def populate_csv_header_combobox(self) -> None:
        """
        Populates the csv header combobox with the headers of the csv file selected in the widget.
        """
        self.combobox_csv_headers_selector.clear()
        csv_file: str = self.get_csv_file_from_widget()

        if not csv_file:
            return

        csv_file_path: Path = Path(csv_file)

        if not self.csv_map_file_is_valid(csv_file=csv_file_path):
            return

        # check if file has at least two columns
        if not csv_file_has_min_column_count(
            csv_file_path=csv_file_path, minimum_column_count=2
        ):
            return
        # check if the first column has integer values
        if not csv_file_column_is_type_integer(
            csv_file_path=csv_file_path, column_idx_to_check=0
        ):
            return

        csv_headers_list: list[str] = get_csv_file_headers_list(
            csv_file_path=csv_file_path, skip_columns_indexes=[0]
        )
        self.combobox_csv_headers_selector.addItems(csv_headers_list)

    def csv_map_file_is_valid(self, csv_file: Path) -> bool:
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

    def csv_map_file_content_is_valid(self, csv_file: Path) -> bool:
        """Check if the csv map file content is valid"""
        if not csv_file_column_is_type_integer(
            csv_file_path=csv_file, column_idx_to_check=0
        ):
            QMessageBox.critical(
                None,
                tr("Csv file error"),
                f"{tr('First column of')} {csv_file.stem} {tr('does not contain only integer values. Please check the csv file.')}",
            )
            return False
        if csv_file_has_duplicates(csv_file_path=csv_file, column_idx_to_check=0):
            QMessageBox.critical(
                None,
                tr("Csv file error"),
                str(
                    f"{tr('First column of')} {csv_file.stem} {tr('contains duplicates. Please check the csv file.')}"
                ),
            )
            return False
        return True

    def populate_mapping_table_from_csv(self) -> None:
        """
        Populates the mapping table with values from a CSV file.

        If the CSV file is invalid or its content is invalid, the method returns without making any changes to the table.

        The mapping between the CSV values and the mapped values is determined by the currently selected column in the CSV file.

        The method updates existing values in the table if they match a CSV value, and appends new rows to the table for CSV values that are not already present.
        """
        csv_file: str = self.get_csv_file_from_widget()

        if not csv_file:
            return

        csv_file_path: Path = Path(csv_file)
        if not self.csv_map_file_is_valid(csv_file=csv_file_path):
            return

        if not self.csv_map_file_content_is_valid(csv_file=csv_file_path):
            return

        csv_mapping_data: list[tuple[int, int]] = self.get_csv_data_mapping_data(
            csv_file_path=csv_file_path,
            mapping_column_idx=self.combobox_csv_headers_selector.currentIndex() + 1,
        )

        for csv_value, csv_mapped_value in csv_mapping_data:
            if self._table_model.value_exists_in_column(
                value=str(csv_value), column_index=0
            ):
                self._table_model.update_value_in_column(
                    first_column_value=str(csv_value),
                    update_column_index=1,
                    new_cell_value=str(csv_mapped_value),
                )
            else:
                self._table_model.append_row(
                    value=str(csv_value), mapped_value=str(csv_mapped_value)
                )

    def get_csv_data_mapping_data(
        self, csv_file_path: Path, mapping_column_idx: int
    ) -> list[tuple[int, int]]:
        """Get the data from the csv file and return it as a list of tuples

        Args:
            mapping_column_idx (int): The column index to use as mapping data

        Returns:
            list[tuple[int,int]]: The csv data as a list of tuples
        """
        csv_data: list[tuple[int, int]] = []
        with open(str(csv_file_path), "r", encoding="utf-8") as csv_file:
            csv_reader = reader(csv_file, delimiter=";")
            next(csv_reader)
            for row in csv_reader:
                try:
                    csv_data.append((int(row[0]), int(row[mapping_column_idx])))
                except ValueError:
                    QMessageBox.critical(
                        None,
                        tr("Csv file value error"),
                        f"{tr('all values of')} {csv_file_path.stem} {tr('are not integers. Please check the csv file.')}",
                    )
                    # TODO : return empty list to be more restrictive ?

        return csv_data

    def update_propertie_value(self):
        """Update le text"""
        self.leText.setText(self._table_model.get_data_as_propertie_list())

    def text(self):
        return self.leText.text()

    def getValue(self):
        return self.leText.text()

    def setValue(self, value):
        self.leText.setText(value)
