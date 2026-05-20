from pathlib import Path

SITUATION_CHART_BASE_CSV_PATH: Path = Path(__file__).parent / "analyse_bretagne_ref.csv"
SITUATION_CHART_BASE_CSV_COLUMNS: list[str] = ["indice_insertion", "indice_effort"]
DEFAULT_COLOR_MAP: str = "Blues"

RESULT_CSV_MANDATORY_ID_EXPLOITATION_COLUMN: str = "exploitation"
RESULT_CSV_MANDATORY_NUMERIC_COLUMNS: list[str] = [
    "tx_boisement_externe",
    "tx_boisement_interne",
    "surface",
    "surface_boisement",
    "surface_arbre",
    "surface_haie",
    "surface_massif",
    "delta_gb",
    "delta_seuil_gb",
]

RESULT_CSV_MANDATORY_COLUMNS: list[str] = [
    RESULT_CSV_MANDATORY_ID_EXPLOITATION_COLUMN,
    "scenario",
] + RESULT_CSV_MANDATORY_NUMERIC_COLUMNS
