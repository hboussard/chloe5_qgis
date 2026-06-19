from pathlib import Path

SITUATION_CHART_BASE_CSV_PATH: Path = (
    Path(__file__).parent / "exploitations_rpg20224_grain_bocager.csv"
)
SITUATION_CHART_CSV_COLUMNS: list[str] = [
    "tx_bois_int",
    "tx_bois_ext",
    "insee",
    "code_epci",
    "code_dep",
    "code_reg",
]
SITUATION_CHART_PLOT_X_COLUMN: str = "tx_bois_ext"
SITUATION_CHART_PLOT_Y_COLUMN: str = "tx_bois_int"
SITUATION_CHART_FILTER_COLUMNS: list[str] = ["code_reg", "code_dep", "code_epci"]
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

RESULT_LAYER_RASTER_PREFIXES: list[str] = [
    "grain_bocager_4classes",
    "type_boisement",
]
RESULT_EA_RASTER_PREFIX: str = "ea_"

RESULT_LAYER_RASTER_EXTENSIONS: list[str] = [".tif"]

RESULT_LAYERS_ROOT_GROUP_NAME: str = "grain bocager exploitation"
RESULT_EXTERNE_FOLDER_NAME: str = "externe"
RESULT_INITIAL_FOLDER_NAME: str = "initial"
RESULT_EXTERNE_GROUP_LABEL: str = "Externe"
RESULT_INITIAL_GROUP_LABEL: str = "Initial"
RESULT_EA_GROUP_LABEL: str = "EA"
