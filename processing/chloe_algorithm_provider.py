from pathlib import Path
from processing.core.ProcessingConfig import ProcessingConfig, Setting
from qgis.core import QgsProcessingProvider, QgsRuntimeProfiler
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon
from .algorithms.landscape_metrics.sliding_algorithm import SlidingAlgorithm
from .algorithms.landscape_metrics.sliding_multi_algorithm import SlidingMultiAlgorithm
from .algorithms.landscape_metrics.selected_algorithm import SelectedAlgorithm
from .algorithms.landscape_metrics.grid_algorithm import GridAlgorithm
from .algorithms.landscape_metrics.map_algorithm import MapAlgorithm
from .algorithms.tools.combine_algorithm import CombineAlgorithm
from .algorithms.tools.search_and_replace_algorithm import SearchAndReplaceAlgorithm
from .algorithms.tools.classification_algorithm import ClassificationAlgorithm
from .algorithms.generate_grid.from_csv_algorithm_multi import FromCSVMultiAlgorithm
from .algorithms.generate_grid.from_csv_algorithm_single import FromCSVSingleAlgorithm
from .helpers.constants import CHLOE_PROVIDER_SUPPORTED_RASTER_EXTENSIONS


class ChloeAlgorithmProvider(QgsProcessingProvider):
    """The ChloeAlgorithmProvider class is the entry point for the CHLOE 5 processing provider."""

    def __init__(self):
        super().__init__()
        self.algs = []

    def load(self):
        """Load the provider, setting up the algorithms and other necessary items."""
        with QgsRuntimeProfiler.profile("Chloe 5 Provider"):
            ProcessingConfig.settingIcons[self.name()] = self.icon()
            ProcessingConfig.addSetting(
                Setting(self.name(), "ACTIVATE_CHLOE5", self.tr("Activate"), True)
            )
            ProcessingConfig.readSettings()
            self.refreshAlgorithms()
        return True

    def unload(self) -> None:
        ProcessingConfig.removeSetting("ACTIVATE_CHLOE5")

    def isActive(self) -> bool:
        """Returns True if the provider is active, False otherwise."""
        return ProcessingConfig.getSetting("ACTIVATE_CHLOE5")

    def setActive(self, active: bool) -> None:
        ProcessingConfig.setSettingValue("ACTIVATE_CHLOE5", active)

    def name(self) -> str:
        """Returns the provider name, which is used to describe the provider within the GUI."""
        return "Chloe 5 - Landscape metrics"

    def longName(self) -> str:
        """Returns the a longer version of the provider name, which can include extra details such as version numbers."""
        # version = ChloeUtils.readableVersion()
        # return 'CHLOE ({})'.format(version)
        return "Chloe 5 - Landscape metrics"

    def id(self) -> str:
        """Returns the unique provider id, used for identifying the provider"""
        return "chloe_5"

    def helpId(self):
        return "chloe_5"

    def icon(self) -> QIcon:
        icon_path: Path = Path(__file__).resolve().parent / "images" / "chloe_icon.png"
        return QIcon(str(icon_path))

    def loadAlgorithms(self):
        """Load the algorithms that belong to this provider."""
        self.algs = [
            SlidingAlgorithm(),
            SlidingMultiAlgorithm(),
            SelectedAlgorithm(),
            CombineAlgorithm(),
            SearchAndReplaceAlgorithm(),
            FromCSVMultiAlgorithm(),
            FromCSVSingleAlgorithm(),
            ClassificationAlgorithm(),
            GridAlgorithm(),
        ]

        [self.addAlgorithm(alg) for alg in self.algs]

    def supportedOutputRasterLayerExtensions(self):
        """Returns a list of supported raster layer extensions."""
        return CHLOE_PROVIDER_SUPPORTED_RASTER_EXTENSIONS

    def supportsNonFileBasedOutput(self):
        """
        CHLOE Provider doesn't support non file based outputs
        """
        return False

    def tr(self, string, context=""):
        if context == "":
            context = "ChloeAlgorithmProvider"
        return QCoreApplication.translate(context, string)
