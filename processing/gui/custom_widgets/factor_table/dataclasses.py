from dataclasses import dataclass
from pathlib import Path


@dataclass
class CombineFactorElement:
    """object to store a combine factor element of the combine factor table"""

    factor_name: str
    layer_name: str
    layer_path: Path
    layer_id: str

    @staticmethod
    def from_string(values: list[str]):
        """utility method to create a CombineFactorElement from a list of string values.
        The order of the values in the array should be : factor_name, layer_name, layer_path, layer_id
        """
        return CombineFactorElement(
            factor_name=values[0],
            layer_name=values[1],
            layer_path=Path(values[2]),
            layer_id=values[3],
        )

    @staticmethod
    def to_string(combine_factor) -> list[str]:
        """utility method to create a list of string values from a CombineFactorElement."""
        return [
            combine_factor.factor_name,
            combine_factor.layer_name,
            str(combine_factor.layer_path),
            combine_factor.layer_id,
        ]


@dataclass
class CombineFactorTableResult:
    """Object to store the result of the combine factor table widget"""

    result_matrix: list[CombineFactorElement]
    combination_formula: str


@dataclass
class LayerInfo:
    """A dataclass to hold information about a layer."""

    layer_path: str
    # layer_id only used for modeler dialog to store the layer id of the layer if it is a modeler input layer
    modeler_input_id: str
