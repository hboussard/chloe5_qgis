from typing import Protocol
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QComboBox,
    QWidget,
    QHBoxLayout,
    QLabel,
)
from .constants import DEFAULT_COLOR_MAP, SITUATION_CHART_BASE_CSV_COLUMNS
from qgis.core import QgsMessageLog, Qgis
from qgis.utils import iface
from dataclasses import dataclass


@dataclass
class HighlightPoint:
    x: float
    y: float
    label: str


class CustomChart(Protocol):
    def set_highlight_points(self, highlight_points: list[HighlightPoint]) -> None:
        """Sets a specific point to highlight on the heatmap."""
        pass

    def draw_chart(self) -> None:
        """Creates a chart and optionally overlays a point."""
        pass

    def set_colormap(self, colormap: str) -> None:
        """set selected colormap"""
        pass

    def get_canvas(self) -> FigureCanvas:
        pass


class SituationChart:
    """Chart base class for matplotlib pcolormesh heatmap"""

    def __init__(self, parent=None) -> None:
        self._parent = parent
        # self._canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self._figure: Figure = Figure(figsize=(5, 3), dpi=100)  # Explicit size & DPI
        self._canvas: FigureCanvas = FigureCanvas(self._figure)
        self._toolbar: NavigationToolbar = NavigationToolbar(self._canvas, None)
        self._ax = self._canvas.figure.subplots()
        self._data = None
        self._color_map: str = DEFAULT_COLOR_MAP
        self._highlight_points: list[HighlightPoint] = []

    def load_csv(self, file_path: str) -> None:
        """Loads data from a CSV file and prepares it for plotting."""
        error_message: str | None = None
        try:
            df = pd.read_csv(file_path, sep=";")
            self._data = df[SITUATION_CHART_BASE_CSV_COLUMNS].values
            self.draw_chart()
        except FileNotFoundError:
            error_message = f"le fichier csv {file_path} est introuvable."
        except pd.errors.EmptyDataError:
            error_message = "Error: The CSV file is empty."
        except pd.errors.ParserError:
            error_message = "Error: There was a problem parsing the CSV file."
        except KeyError as e:
            error_message = f"Error: Missing columns in the CSV file - {e}"
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
        finally:
            if error_message:
                QgsMessageLog.logMessage(error_message, level=Qgis.Critical)
                iface.messageBar().pushMessage(
                    "Erreur",
                    error_message,
                    level=Qgis.Critical,
                )

    def set_highlight_points(self, highlight_points: list[HighlightPoint]) -> None:
        """Sets a specific point to highlight on the heatmap."""
        self._highlight_points = highlight_points
        self.draw_chart()

    def draw_chart(self) -> None:
        """Creates a heatmap using pcolormesh and optionally overlays a point."""
        if self._data is None or len(self._data) == 0:
            return

        self._ax.clear()

        # Extract X and Y values from the data
        x = self._data[:, 0]
        y = self._data[:, 1]

        # Create a 2D histogram density plot
        bins = 50  # Adjust bin size for better resolution
        hist, x_edges, y_edges = np.histogram2d(x, y, bins=bins, density=True)

        # Plot heatmap using imshow with 'Blues' colormap
        # im = self._ax.imshow(
        #     hist.T,
        #     origin="lower",
        #     cmap=self._color_map,
        #     extent=[x.min(), x.max(), y.min(), y.max()],
        #     interpolation="bilinear",
        #     aspect="auto",
        # )
        # Plot heatmap using imshow with 'Blues' colormap
        hb = self._ax.hexbin(
            x,
            y,
            gridsize=150,
            cmap=self._color_map,
            mincnt=1,
            edgecolors="none",
            alpha=1,
        )
        # add median line of the hb values
        median_x = np.median(x)
        median_y = np.median(y)
        self._ax.axvline(x=median_x, color="grey", linestyle="--", linewidth=1)
        self._ax.axhline(y=median_y, color="grey", linestyle="--", linewidth=1)
        # Overlay the specific point if set
        if self._highlight_points:
            for point in self._highlight_points:
                # show point with coordinates as label

                hx, hy = point.x, point.y
                self._ax.axvline(hx, color="black", linestyle="-", linewidth=1)
                self._ax.axhline(hy, color="black", linestyle="-", linewidth=1)
                self._ax.scatter(hx, hy, color="black", s=100, label=point.label)
                # Add x value at x-axis level
                self._ax.text(
                    hx,
                    self._ax.get_ylim()[0],
                    f"{hx:.2f}",
                    fontsize=8,
                    ha="center",
                    va="top",
                    rotation=45,
                    style="italic",
                )
                # Add y value at y-axis level
                self._ax.text(
                    self._ax.get_xlim()[0],
                    hy,
                    f"{hy:.2f}",
                    fontsize=8,
                    ha="right",
                    va="center",
                    rotation=0,
                    style="italic",
                )

        # Labels and title
        self._ax.set_xlabel("Taux de boisement externe")
        self._ax.set_ylabel("Taux de boisement interne")
        self._ax.set_title("Situation de l'exploitation")
        # Add legend
        self._ax.legend()
        self._figure.tight_layout()
        self._canvas.draw()

    def set_colormap(self, colormap: str) -> None:
        self._color_map = colormap
        self.draw_chart()

    def get_canvas(self) -> FigureCanvas:
        """get canvas"""
        return self._canvas

    def get_toolbar(self) -> NavigationToolbar:
        """get toolbar"""
        return self._toolbar


class EvolutionChart:
    """Chart base class for matplotlib pcolormesh heatmap"""

    def __init__(self, parent=None) -> None:
        self._parent = parent
        self._figure = Figure(figsize=(5, 3), dpi=100)  # Explicit size & DPI
        self._canvas = FigureCanvas(self._figure)
        self._toolbar = NavigationToolbar(self._canvas, None)
        self._ax = self._canvas.figure.subplots()
        self._color_map: str = DEFAULT_COLOR_MAP
        self._highlight_point: list[HighlightPoint] = []

    def set_highlight_points(self, highlight_points: list[HighlightPoint]) -> None:
        """Sets a specific point to highlight on the heatmap."""
        self._highlight_point = highlight_points
        self.draw_chart()

    def get_x_min(self) -> float:
        """get x min from highlight point"""
        if self._highlight_point:
            return min(point.x for point in self._highlight_point)
        return 0

    def get_x_max(self) -> float:
        """get x max from highlight point"""
        if self._highlight_point:
            return max(point.x for point in self._highlight_point)
        return 0

    def get_y_min(self) -> float:
        """get y min from highlight point"""
        if self._highlight_point:
            return min(point.y for point in self._highlight_point)
        return 0

    def get_y_max(self) -> float:
        """get y max from highlight point"""
        if self._highlight_point:
            return max(point.y for point in self._highlight_point)
        return 0

    def draw_chart(self) -> None:
        """Creates a heatmap using pcolormesh and optionally overlays a point."""

        self._ax.clear()

        # Create a grid
        x_bins = np.linspace(0, self.get_x_max(), 20)
        y_bins = np.linspace(0, self.get_y_max(), 20)

        # Overlay the specific point if set
        if self._highlight_point:
            [
                self._ax.scatter(
                    point.x,
                    point.y,
                    # color="black",
                    # edgecolor="white",
                    s=100,
                    label=point.label,
                    alpha=0.5,
                )
                for point in self._highlight_point
            ]

        # Labels and title
        self._ax.set_xlabel("Delta grain bocager")
        self._ax.set_ylabel("Delta seuil grain bocager")
        self._ax.set_title("Situation de l'exploitation")
        # Add legend
        self._ax.legend()
        self._figure.tight_layout()
        self._canvas.draw()

    def set_colormap(self, colormap: str) -> None:
        self._color_map = colormap
        self.draw_chart()

    def get_canvas(self) -> FigureCanvas:
        """get canvas"""
        return self._canvas

    def get_toolbar(self) -> NavigationToolbar:
        """get toolbar"""
        return self._toolbar


class ChartToolBarWithColormap(QWidget):
    """Chart tool bar with colormap combobox"""

    def __init__(
        self,
        linked_chart: CustomChart,
        parent=None,
        default_color_map: str = DEFAULT_COLOR_MAP,
    ) -> None:
        super().__init__(parent)
        self._linked_chart: CustomChart = linked_chart
        self._default_color_map = default_color_map
        self.chart_layout: QHBoxLayout = QHBoxLayout(self)
        self.setup_toolbar()
        self.setup_color_map_combobox()

    def setup_toolbar(self):
        toolbar: NavigationToolbar = NavigationToolbar(
            self._linked_chart.get_canvas(), self
        )
        self.chart_layout.addWidget(toolbar)

    def setup_color_map_combobox(self):
        color_map_combobox: ColormapsCombobox = ColormapsCombobox(
            self._linked_chart, self, self._default_color_map
        )
        self.chart_layout.addWidget(color_map_combobox)


class ChartToolBar(QWidget):
    """Chart tool bar"""

    def __init__(
        self,
        linked_chart: CustomChart,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._linked_chart: CustomChart = linked_chart
        self.chart_layout: QHBoxLayout = QHBoxLayout(self)
        self.setup_toolbar()

    def setup_toolbar(self):
        toolbar: NavigationToolbar = NavigationToolbar(
            self._linked_chart.get_canvas(), self
        )
        self.chart_layout.addWidget(toolbar)


class ColormapsCombobox(QWidget):
    """Combobox for matplotlib colormaps"""

    def __init__(
        self,
        linked_chart: CustomChart,
        parent=None,
        default_color_map: str = DEFAULT_COLOR_MAP,
    ) -> None:
        """add a combobox with a label"""
        super().__init__(parent)
        self._colormaps = [
            "Blues",
            "Greys",
            "Purples",
            "Greens",
            "Oranges",
            "Reds",
            "YlOrBr",
            "YlOrRd",
            "OrRd",
            "PuRd",
            "RdPu",
            "BuPu",
            "GnBu",
            "PuBu",
            "YlGnBu",
            "PuBuGn",
            "BuGn",
            "YlGn",
        ]  # plt.colormaps()
        self.default_color_map = default_color_map
        self._linked_chart = linked_chart

        self.init_color_map_gui()
        self.setLayout(self._layout)

    def init_color_map_gui(self):
        # add label
        self._label = QLabel("Couleurs graphique : ")
        # add combobox
        self._combobox = QComboBox()
        # add to layout
        self._layout = QHBoxLayout()
        self._layout.addWidget(self._label)
        self._layout.addWidget(self._combobox)
        # add items
        self._combobox.addItems(self._colormaps)
        # set delegate
        self._combobox.currentIndexChanged.connect(self._on_selection_changed)
        self.set_colormap(self.default_color_map)

    def _on_selection_changed(self):
        """set colormap of linked chart"""
        if self.get_colormap():
            self._linked_chart.set_colormap(self.get_colormap())

    def get_colormap(self) -> str:
        """get selected colormap"""
        return self._combobox.currentText()

    def set_colormap(self, colormap: str) -> None:
        """set selected colormap"""
        self._combobox.setCurrentText(colormap)
