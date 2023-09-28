from enum import Enum


# parameters options enums


class AnalyzeType(Enum):
    """Analyze type enum"""

    THRESHOLD = "threshold"
    WEIGHTED_DISTANCE = "weighted distance"


class DistanceType(Enum):
    """Distance type enum"""

    EUCLIDIAN_DISTANCE = "euclidian distance"
    FUNCTIONAL_DISTANCE = "functional distance"


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
