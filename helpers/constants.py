from pathlib import Path

CHLOE_JAR_NAME: str = "chloe5-0.0.1.jar"
CHLOE_JAR_PATH: str = rf"-jar bin/{CHLOE_JAR_NAME}"
CHLOE_WORKING_DIRECTORY_PATH: Path = Path(__file__).parent.parent / "Chloe"
CHLOE_PLUGIN_PATH: Path = Path(__file__).parent.parent

CHLOE_RASTER_FILE_EXTENSIONS: list[str] = [".asc", ".tif"]
