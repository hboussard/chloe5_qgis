# -*- coding: utf-8 -*-

import csv
from dataclasses import dataclass
from pathlib import Path

DATA_DIR: Path = Path(__file__).parent / "data"


@dataclass(frozen=True)
class Region:
    """Région administrative française."""

    code_reg: str
    libelle_reg: str

    def combo_label(self) -> str:
        return f"{self.code_reg} - {self.libelle_reg}"

    def combo_code(self) -> str:
        return self.code_reg


@dataclass(frozen=True)
class Departement:
    """Département français rattaché à une région."""

    code_dep: str
    lib_dep: str
    code_reg: str

    def combo_label(self) -> str:
        return f"{self.code_dep} - {self.lib_dep}"

    def combo_code(self) -> str:
        return self.code_dep


@dataclass(frozen=True)
class Epci:
    """EPCI rattaché à un département et à une région."""

    code_epci: str
    lib_epci: str
    nature: str
    code_reg: str
    code_dep: str

    def combo_label(self) -> str:
        return f"{self.code_epci} - {self.lib_epci}"

    def combo_code(self) -> str:
        return self.code_epci


@dataclass(frozen=True)
class SituationSelection:
    """Selection state emitted by the situation selector widget.

    A ``None`` value means the user kept the ``toutes`` entry for that level.
    """

    code_reg: str | None = None
    code_dep: str | None = None
    code_epci: str | None = None


def load_regions(csv_path: Path = DATA_DIR / "regions.csv") -> list[Region]:
    """Load the list of regions from the bundled CSV file."""
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            Region(
                code_reg=row["DREG_C_COD"],
                libelle_reg=row["DREG_L_LIB"],
            )
            for row in reader
        ]


def load_departements(
    csv_path: Path = DATA_DIR / "departement.csv",
) -> list[Departement]:
    """Load the list of departements from the bundled CSV file."""
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            Departement(
                code_dep=row["DDEP_C_COD"],
                lib_dep=row["DDEP_L_LIB"],
                code_reg=row["DREG_C_COD"],
            )
            for row in reader
        ]


def load_epcis(csv_path: Path = DATA_DIR / "epci.csv") -> list[Epci]:
    """Load the list of EPCIs from the bundled CSV file."""
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            Epci(
                code_epci=row["EPCI_CODE"],
                lib_epci=row["EPCI"],
                nature=row["NATURE"],
                code_reg=row["REG_CODE"],
                code_dep=row["DEPT_CODE"],
            )
            for row in reader
        ]
