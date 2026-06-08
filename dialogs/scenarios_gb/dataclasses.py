from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ScenarioResult:
    """Dataclass to store the results of a scenario"""

    id_exploitation: str
    scenario_name: str
    tx_boisement_externe: float
    tx_boisement_interne: float
    surface: float
    surface_boisement: float
    surface_arbre: float
    surface_haie: float
    surface_massif: float
    delta_gb: float
    delta_seuil_gb: float


@dataclass
class ScenarioGBProperties:
    scenario_name: str
    parcellaire: Path
    attribut_code_ea: str
    code_ea: str
    bocage: Path
    amenagement: Path | None
    attribut_scenario: str | None
    output_folder: Path
    grain_bocager_cellsize: float
    grain_bocager_window_radius: float
    grain_bocager_thresholds: list[float]
    _file_path: Path = Path()

    def create_properties(self) -> list[str]:

        parcellaire: str = str(self.parcellaire).replace("\\", "/")
        bocage: str = str(self.bocage).replace("\\", "/")
        amenagement: str = (
            str(self.amenagement).replace("\\", "/") if self.amenagement else ""
        )
        output_folder: str = str(self.output_folder).replace("\\", "/")

        lst_properties: list[str] = [
            "procedure=grain_bocager_exploitation",
            "export_map=true",
            f"parcellaire={parcellaire}",
            f"attribut_code_ea={self.attribut_code_ea}",
            f"code_ea={self.code_ea}",
            f"bocage={bocage}",
            f"grain_bocager_cellsize={self.grain_bocager_cellsize}",
            f"grain_bocager_window_radius={self.grain_bocager_window_radius}",
            f"thresholds={{{';'.join(map(str, self.grain_bocager_thresholds))}}}",
            f"output_folder={output_folder}",
            f"scenario={self.scenario_name}",
            "force=true",
        ]

        if self.amenagement != Path():
            lst_properties.append(f"amenagement={amenagement}")
            lst_properties.append(f"attribut_scenario={self.attribut_scenario}")

        return lst_properties

    def get_properties_file_path(self) -> Path:
        return self._file_path

    def create_properties_file(self):
        suffix: str = datetime.now().strftime("%d-%m-%Y_%H-%M-%S.%f")
        file_path: Path = (
            self.output_folder / f"{self.scenario_name}_{suffix}.properties"
        )
        self._file_path = file_path
        with open(self.get_properties_file_path(), "w", encoding="utf-8") as f:
            f.write("\n".join(self.create_properties()))
