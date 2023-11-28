from dataclasses import dataclass
from typing import Union
from pandas import Interval
from qgis.PyQt.QtCore import QRegExp
from qgis.PyQt.QtWidgets import (
    QMessageBox,
)


DOMAIN_REGEX: str = r"[\[\]](-?\d+\.?\d*)?,(-?\d+\.?\d*)?[\[\]]"


@dataclass
class DomainValue:
    first_value: Union[float, None]
    second_value: Union[float, None]
    left_bound: str
    right_bound: str

    def __post_init__(self):
        if self.first_value is not None and self.second_value is not None:
            if self.first_value > self.second_value:
                raise ValueError(
                    f"Domain value init error : first value should be less than the second value. Got {self.first_value} and {self.second_value}"
                )

    def __str__(self) -> str:
        return f"{self.left_bound}{self.first_value if self.first_value is not None else ''},{self.second_value if self.second_value is not None else ''}{self.right_bound}"

    def to_pandas_interval(self) -> Interval:
        """
        Converts the classification table interval to a pandas Interval object.

        Returns:
            Interval: The pandas Interval object representing the interval.
        """
        first_value = (
            self.first_value if self.first_value is not None else -float("inf")
        )
        second_value = (
            self.second_value if self.second_value is not None else float("inf")
        )
        if self.left_bound == "]" and self.right_bound == "]":
            closed = "right"
        elif self.left_bound == "[" and self.right_bound == "[":
            closed = "left"
        elif self.left_bound == "[" and self.right_bound == "]":
            closed = "both"
        else:
            closed = "neither"

        return Interval(left=first_value, right=second_value, closed=closed)


def from_string_to_domain(value: str) -> Union[DomainValue, None]:
    """
    Converts a string to a DomainValue object.

    Args:
        value (str): The string to convert assuming .

    Returns:
        DomainValue: The DomainValue object.
    """
    regex = QRegExp(DOMAIN_REGEX)
    regex.exactMatch(value)
    if not regex.exactMatch(value):
        QMessageBox.warning(
            None,
            "Invalid domain value",
            "The domain value should follow the interval syntax. Examples: [0,1[ or ],-1] or [2,[.",
        )
        return None

    first_value: str = regex.cap(1)
    second_value: str = regex.cap(2)
    left_bound: str = regex.cap(0)[0]
    right_bound: str = regex.cap(0)[-1]

    # swap bounds if needed
    if left_bound == "[" and not first_value:
        left_bound = "]"
    if right_bound == "]" and not second_value:
        right_bound = "["

    if not first_value and not second_value:
        QMessageBox.warning(
            None,
            "Invalid domain value",
            "At least one value should be set in the domain",
        )
        return None

    try:
        return DomainValue(
            first_value=float(first_value) if first_value else None,
            second_value=float(second_value) if second_value else None,
            left_bound=left_bound,
            right_bound=right_bound,
        )
    except ValueError as e:
        QMessageBox.warning(
            None,
            "Invalid domain value",
            f"{e}",
        )
        return None
