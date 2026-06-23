from ..dataclasses import ScenarioResult
from qgis.PyQt.QtGui import (
    QStandardItemModel,
    QStandardItem,
)
from qgis.PyQt.QtCore import Qt, pyqtSignal


class ResultsTableModel(QStandardItemModel):
    # custom signal when model is updated
    signal_model_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(
            ["Scénario", "Tx bois ext", "Tx bois int", "delta gb", "delta seuil gb"]
        )

        # Enable sorting
        self.setSortRole(Qt.DisplayRole)

        self.rowsInserted.connect(self.model_updated)
        self.dataChanged.connect(self.model_updated)
        self.rowsRemoved.connect(self.model_updated)

        self._data: list[ScenarioResult] = []

    def model_updated(self) -> None:
        """Emit signal when model is updated"""
        self.signal_model_updated.emit()

    def set_data(self, data: list[ScenarioResult]) -> None:
        self._data = data
        self.setRowCount(0)
        for result in self._data:
            row: list[QStandardItem] = []
            row.append(QStandardItem(str(result.scenario_name)))
            for value in (
                result.tx_boisement_externe,
                result.tx_boisement_interne,
                result.delta_gb,
                result.delta_seuil_gb,
            ):
                item = QStandardItem()
                item.setData(float(value), Qt.DisplayRole)
                row.append(item)
            self.appendRow(row)

    def get_data(self) -> list[ScenarioResult]:
        return self._data

    def clear_data(self):
        """clear the model data"""
        self.removeRows(0, self.rowCount())
