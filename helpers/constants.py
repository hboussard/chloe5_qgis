from pathlib import Path
from qgis.core import QgsApplication

CHLOE_JAR_NAME: str = "chloe5-0.0.1.jar"
CHLOE_JAR_PATH: str = rf"-jar -Xmx4g -Xss8m  bin\{CHLOE_JAR_NAME}"
CHLOE_WORKING_DIRECTORY_PATH: Path = Path(__file__).parent.parent / "Chloe"
CHLOE_PLUGIN_PATH: Path = Path(__file__).parent.parent
