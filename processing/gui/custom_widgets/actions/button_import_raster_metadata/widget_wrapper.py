from pathlib import Path
from typing import Any, Union
from qgis.PyQt.QtWidgets import QPushButton, QFileDialog, QMessageBox
from .....algorithms.helpers.constants import (
    WIDTH,
    HEIGHT,
    XMIN,
    YMIN,
    CELL_SIZE,
    NODATA_VALUE,
    OUTPUT_CRS,
)
from ...helpers import (
    replace_param_widget_value,
)

from ..widget_wrapper import ChloeActionWidgetWrapper

from .file_parser_strategy import (
    FileParserStrategy,
    RasterMetadataData,
    TxtFileParser,
    RasterFileParser,
)


class ChloeImportRasterMetadataButtonWidgetWrapper(ChloeActionWidgetWrapper):
    """Widget wrapper for the "Import header" button in the "From CSV" algorithm dialog.
    This wrapper is thightly coupled with the "From CSV" algorithm dialog."""

    def createWidget(self, button_title: str):
        """Add a single button to the wrapper"""

        self.file_parsers: dict[str, FileParserStrategy] = {
            ".txt": TxtFileParser(),
            ".asc": RasterFileParser(),
            ".tif": RasterFileParser(),
        }

        widget = QPushButton(self.tr(button_title))

        widget.clicked.connect(self.select_file)
        return widget

    def select_file(self) -> None:
        """
        Opens a dialog to select a file and updates the algorithm widgets with the raster metadata.

        Returns:
            None
        """
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setNameFilters(
            ["Text files (*.txt)", "ASCII Grid files (*.asc)", "GeoTiff files (*.tif)"]
        )
        file_dialog.selectNameFilter("text (*.txt)")

        file_names: list[str] = []

        if file_dialog.exec_():
            file_names: list[str] = file_dialog.selectedFiles()

        if not file_names:
            return

        file_path: Path = Path(file_names[0])

        self.update_algorithm_widgets_with_file_raster_metadata(file_path)

    def update_algorithm_widgets_with_file_raster_metadata(
        self, file_path: Path
    ) -> None:
        """
        Updates the algorithm parameter widgets with the metadata extracted from the file.

        Args:
            file_path (Path): The path to the file containing the raster metadata.
        """
        if file_path == Path() or not file_path.exists():
            QMessageBox.warning(
                self.dialog,
                self.tr("File selected do not exist"),
                self.tr("Please select a file"),
            )
            return

        raster_metadata: Union[
            RasterMetadataData, None
        ] = self.get_file_raster_metadata(file_path)
        # replace widget values with the data
        if raster_metadata is None:
            return
        self.replace_algorithm_param_widgets_values(raster_metadata)

    def get_file_raster_metadata(
        self, file_path: Path
    ) -> Union[RasterMetadataData, None]:
        """
        Analyzes the file at the given file path and returns its raster metadata.

        Args:
            file_path (Path): The path to the file to parse.

        Returns:
            Union[RasterMetadataData, None]: The raster metadata extracted from the file, or None if no metadata is found.
        """
        file_extension: str = file_path.suffix

        parser = self.file_parsers.get(file_extension)

        if parser is None:
            raise ValueError(
                f"No parser available for files with extension {file_extension}"
            )

        return parser.get_raster_metadata(file_path)

    def replace_algorithm_param_widgets_values(
        self, raster_metadata: RasterMetadataData
    ):
        """
        Replaces the values of the algorithm parameter widgets with the corresponding values from the given file raster metadata.

        Args:
            raster_metadata (RasterMetadataData): The file raster metadata containing the values to replace the parameter widgets with.
        """
        param_mapping: dict[str, Any] = {
            WIDTH: raster_metadata.width,
            HEIGHT: raster_metadata.height,
            XMIN: raster_metadata.xmin,
            YMIN: raster_metadata.ymin,
            CELL_SIZE: raster_metadata.cell_size,
            NODATA_VALUE: raster_metadata.nodata_value,
            OUTPUT_CRS: raster_metadata.crs,
        }

        for param_name, value in param_mapping.items():
            replace_param_widget_value(
                algorithm_dialog=self.dialog,
                dialog_type=self.dialogType,
                param_name=param_name,
                value=value,
            )
