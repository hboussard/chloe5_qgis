from pathlib import Path
from dataclasses import dataclass
from typing import Protocol, Union
from qgis.PyQt.QtWidgets import QMessageBox
from osgeo import gdal


@dataclass
class RasterMetadataData:
    """
    Represents raster metadata.

    Attributes:
        width (int): raster number of columns.
        height (int): raster number of rows.
        xmin (float): The minimum x-coordinate of the raster.
        ymin (float): The minimum y-coordinate of the raster.
        cell_size (float): raster cell size.
        nodata_value (Union[int, None]): Raster nodata value , or None if not specified.
    """

    width: int
    height: int
    xmin: float
    ymin: float
    cell_size: float
    nodata_value: Union[int, None]


class FileParserStrategy(Protocol):
    """
    A strategy for parsing a file and returning its raster metadata informations.

    Methods:
    --------
    get_raster_metadata(file_path: Path) -> Union[RasterMetadataData, None]:
        Analyzes the given file and returns the raster metadata extracted from this file, or None if the file
        does not contain metadata.
    """

    def get_raster_metadata(self, file_path: Path) -> Union[RasterMetadataData, None]:
        ...


class TxtFileParser:
    """A class for parsing raster metadata from a txt file.

    Attributes:
        None

    Methods:
        get_raster_metadata(file_path: Path) -> Union[RasterMetadataData, None]:
            Parses the raster metadata from the given txt file.

    """

    def get_raster_metadata(self, file_path: Path) -> Union[RasterMetadataData, None]:
        """Logic for parsing a txt file
         when reading the file it should have this format :
        #parameter file generated with APILand
        #Fri Nov 10 17:06:17 CET 2023
        miny=6824050.142000002
        height=1538
        minx=356062.7354999971
        cellsize=10.0
        noDataValue=-1
        width=1404
        maxy=6839430.142000002
        maxx=370102.7354999971"""

        # initialize the variables
        width: int = 0
        height: int = 0
        xmin: float = 0.0
        ymin: float = 0.0
        cell_size: float = 0.0
        nodata_value: Union[int, None] = None

        with open(str(file_path), "r", encoding="utf-8") as infile:
            # check if file is empty
            first_line = infile.readline()
            if not first_line:
                return None
            # check each line and get the values based on the first element until the first '='
            lines = infile.readlines()
            for line in lines:
                if line.startswith("#"):
                    continue
                else:
                    line = line.strip()
                    if line:
                        line = line.split("=")
                        try:
                            if line[0] == "width":
                                width = int(line[1])
                            elif line[0] == "height":
                                height = int(line[1])
                            elif line[0] == "minx":
                                xmin = float(line[1])
                            elif line[0] == "miny":
                                ymin = float(line[1])
                            elif line[0] == "cellsize":
                                cell_size = float(line[1])
                            elif line[0] == "noDataValue":
                                nodata_value = int(line[1])
                            else:
                                continue
                        except ValueError:
                            # log the message to a QMessage box and explicitly tell for what element there is a conversion error
                            QMessageBox.critical(
                                None,
                                "Error",
                                f"Could not convert value {line[1]} for {line[0]} to the expected type",
                            )
                            return None
        return RasterMetadataData(
            width=width,
            height=height,
            xmin=xmin,
            ymin=ymin,
            cell_size=cell_size,
            nodata_value=nodata_value,
        )


class RasterFileParser:
    """
    A class for parsing raster files and extracting metadata.

    Attributes:
        None

    Methods:
        get_raster_metadata: Extracts metadata from a raster file.
    """

    def get_raster_metadata(self, file_path: Path) -> Union[RasterMetadataData, None]:
        # Logic for parsing a raster file
        dataset = gdal.Open(str(file_path))  # DataSet
        if dataset is None:
            return None

        try:
            width = int(dataset.RasterXSize)
            height = int(dataset.RasterYSize)
            xmin = float(dataset.GetGeoTransform()[0])
            ymin = float(dataset.GetGeoTransform()[3])
            cell_size = int(dataset.GetGeoTransform()[1])
            nodata_value: Union[int, None] = dataset.GetRasterBand(1).GetNoDataValue()
            return RasterMetadataData(
                width=width,
                height=height,
                xmin=xmin,
                ymin=ymin,
                cell_size=cell_size,
                nodata_value=nodata_value,
            )
        except ValueError as e:
            # log the message to a QMessage box and explicitly tell for what element there is a conversion error
            QMessageBox.critical(
                None,
                "Error",
                f"Could not convert value {e} to the expected type",
            )
            return None
