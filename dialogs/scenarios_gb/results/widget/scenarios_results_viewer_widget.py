# -*- coding: utf-8 -*-


from pathlib import Path
from qgis.PyQt.QtWidgets import (
    QWidget,
)
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSortFilterProxyModel
from ..constants import SITUATION_CHART_BASE_CSV_PATH
from ..charts import (
    ChartToolBarWithColormap,
    EvolutionChart,
    SituationChart,
    HighlightPoint,
    ChartToolBar,
)
from ..helpers import analyse_results_directory
from ...dataclasses import ScenarioResult
from ..results_table_model import ResultsTableModel

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(
    Path(__file__).parent / "scenarios_result_viewer_widget.ui"
)


class ScenariosResultViewerWidget(QWidget, FORM_CLASS):

    def __init__(self, parent=None):
        """constructor"""
        super(ScenariosResultViewerWidget, self).__init__(parent)
        self._parent = parent

        # self.scenarios_history: list[ScenarioResult] = []
        self._situation_chart: SituationChart = SituationChart(self)
        self._evolution_chart: EvolutionChart = EvolutionChart(self)
        self.results_table_model = ResultsTableModel()
        self.results: list[ScenarioResult] = []
        self.result_directory_path: Path = Path()

        # Setup Ui
        self.setupUi(self)
        self.setup_gui()

    def setup_gui(self) -> None:
        """setup gui widget properties"""
        self.setup_exploitation_situation_chart()
        self.setup_evolution_grain_chart()
        self.setup_results_table()
        self.comboBox_id_exploitation.currentIndexChanged.connect(
            self.refresh_results_tab
        )

    def setup_exploitation_situation_chart(self) -> None:
        """setup exploitation situation chart"""
        # adding canvas to the layout
        self._situation_chart.load_csv(str(SITUATION_CHART_BASE_CSV_PATH))

        situation_tool_bar: ChartToolBarWithColormap = ChartToolBarWithColormap(
            self._situation_chart, self
        )
        situation_tool_bar.setMaximumSize(16777215, 60)
        # adding canvas to the layout
        self.verticalLayout_results_situation.addWidget(
            self._situation_chart.get_canvas()
        )
        self.verticalLayout_results_situation.addWidget(situation_tool_bar)

    def setup_evolution_grain_chart(self) -> None:
        """setup exploitation situation result graph"""
        # adding canvas to the layout

        evolution_tool_bar: ChartToolBar = ChartToolBar(self._evolution_chart, self)
        evolution_tool_bar.setMaximumSize(16777215, 60)
        # adding canvas to the layout
        self.verticalLayout_results_evolution_grain.addWidget(
            self._evolution_chart.get_canvas()
        )
        self.verticalLayout_results_evolution_grain.addWidget(evolution_tool_bar)

    def setup_results_table(self) -> None:
        """setup results table"""
        sortable_proxy_model = QSortFilterProxyModel()
        sortable_proxy_model.setSourceModel(self.results_table_model)
        self.tableView_results.setSortingEnabled(True)
        self.tableView_results.setModel(sortable_proxy_model)

    def set_result_directory_path(self, result_directory_path: Path) -> None:
        """Set the result directory path"""
        self.result_directory_path = result_directory_path
        # set results by analysing the files in the result directory so the results can be used to populate the id_exploitation_combobox
        self.set_results()
        #  get list of id exploitation
        self.populate_id_exploitation_combobox()

    def set_selected_exploitation_id(self, id_exploitation: str) -> None:
        """Set the selected exploitation id"""
        if id_exploitation not in set(
            [result.id_exploitation for result in self.results]
        ):
            # print(f"id_exploitation {id_exploitation} not in {self.results}")
            self.comboBox_id_exploitation.setCurrentIndex(-1)
            return
        self.comboBox_id_exploitation.setCurrentText(id_exploitation)

    def refresh_results_tab(self):
        """Update results tab with the results of the last process"""
        # reset results to refresh results if any scenario has been added meanwhile
        self.set_results()
        self.label_results_exploitation_id.setText(
            f"Résultats pour l'exploitation {self.comboBox_id_exploitation.currentText()}"
        )
        # filter results by id_exploitation
        results: list[ScenarioResult] = []

        if self.comboBox_id_exploitation.currentIndex() > -1:
            results = [
                result
                for result in self.results
                if result.id_exploitation == self.comboBox_id_exploitation.currentText()
            ]
        self.update_evolution_chart_from_results(results)
        self.update_situation_chart_from_results(results)
        self.update_results_table(results)

    def set_results(self) -> None:
        # reset results to empty list
        self.results = []

        if self.result_directory_path.exists():
            self.results = analyse_results_directory(
                results_directory=self.result_directory_path,
            )

    def update_evolution_chart_from_results(self, results: list[ScenarioResult]):
        """Update graph from results"""
        highlight_points_evolution: list[HighlightPoint] = []
        for result in results:
            highlight_points_evolution.append(
                HighlightPoint(
                    result.delta_gb,
                    result.delta_seuil_gb,
                    result.scenario_name,
                )
            )
        self._evolution_chart.set_highlight_points(highlight_points_evolution)
        self._evolution_chart.draw_chart()

    def update_situation_chart_from_results(self, results: list[ScenarioResult]):
        """Update graph from results"""
        highlight_points_situation: list[HighlightPoint] = []
        for result in results:
            if result.scenario_name == "initial":
                highlight_points_situation.append(
                    HighlightPoint(
                        result.tx_boisement_externe,
                        result.tx_boisement_interne,
                        result.scenario_name,
                    )
                )
        self._situation_chart.set_highlight_points(highlight_points_situation)
        self._situation_chart.draw_chart()

    def update_results_table(self, results: list[ScenarioResult]):
        """Update results table"""
        self.results_table_model.set_data(results)

    def populate_id_exploitation_combobox(self) -> None:
        """populate id exploitation combobox"""
        self.comboBox_id_exploitation.clear()
        # get a set of id_exploitation
        id_exploitation_set: set[str] = set(
            result.id_exploitation for result in self.results
        )

        self.comboBox_id_exploitation.addItems(id_exploitation_set)
