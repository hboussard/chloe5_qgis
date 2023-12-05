from enum import Enum


# parameters options enums


class MimeType(Enum):
    """Mime type enum"""

    GEOTIFF = "GEOTIFF"
    ASCII_GRID = "ASCII GRID"


class AnalyzeType(Enum):
    """Analyze type enum"""

    THRESHOLD = "THRESHOLD"
    WEIGHTED = "WEIGHTED"


class AnalyzeTypeFastMode(Enum):
    """Analyze type enum for fast mode"""

    FAST_GAUSSIAN = "FAST GAUSSIAN"
    FAST_SQUARE = "FAST SQUARE"


class DistanceType(Enum):
    """Distance type enum"""

    EUCLIDIAN = "Euclidian"
    FUNCTIONAL = "Functional"


class WindowShapeType(Enum):
    """Window Shape type enum"""

    CIRCLE = "CIRCLE"
    SQUARE = "SQUARE"
    FUNCTIONAL = "FUNCTIONAL"


class ShortWindowShapeType(Enum):
    """Short window shape type enum"""

    CIRCLE = "cr"
    SQUARE = "sq"
    FUNCTIONAL = "fn"
