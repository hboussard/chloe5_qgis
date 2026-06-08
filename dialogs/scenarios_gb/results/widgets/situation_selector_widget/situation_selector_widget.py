# -*- coding: utf-8 -*-

from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import QComboBox, QWidget

from ....widgets.completer_combobox_widget import CompleterComboBox
from .situation_entities import (
    Departement,
    Epci,
    Region,
    SituationSelection,
    load_departements,
    load_epcis,
    load_regions,
)

FORM_CLASS, _ = uic.loadUiType(Path(__file__).parent / "situation_selector_widget.ui")

ALL_LABEL: str = "toutes"


def _fill_combo_model(
    model: QStandardItemModel,
    items: Iterable[Region | Departement | Epci],
    all_label: str = ALL_LABEL,
) -> None:
    """Populate ``model`` with a leading ``all_label`` row then one row per item.

    The display role holds the formatted label and the user role holds the code
    string (or ``None`` for the leading row).
    """
    model.clear()
    head = QStandardItem(all_label)
    head.setData(None, Qt.UserRole)
    model.appendRow(head)
    for item in items:
        row = QStandardItem(item.combo_label())
        row.setData(item.combo_code(), Qt.UserRole)
        model.appendRow(row)


class ScenariosSituationSelectorWidget(QWidget, FORM_CLASS):
    """Cascading région/département/EPCI selector backed by bundled CSVs."""

    selection_changed = pyqtSignal(SituationSelection)
    comboBox_epci: CompleterComboBox

    def __init__(self, parent=None):
        """constructor"""
        super(ScenariosSituationSelectorWidget, self).__init__(parent)
        self._parent = parent

        self._regions: list[Region] = []
        self._departements: list[Departement] = []
        self._epcis: list[Epci] = []

        self._region_model: QStandardItemModel = QStandardItemModel(self)
        self._departement_model: QStandardItemModel = QStandardItemModel(self)
        self._epci_model: QStandardItemModel = QStandardItemModel(self)

        self.setupUi(self)
        self.setup_gui()

    def setup_gui(self) -> None:
        """setup gui widget properties"""
        self._regions = load_regions()
        self._departements = load_departements()
        self._epcis = load_epcis()

        self._setup_epci_combobox()

        self.comboBox_region.setModel(self._region_model)
        self.comboBox_departement.setModel(self._departement_model)
        self.comboBox_epci.setModel(self._epci_model)
        self.comboBox_epci.setCompleterFilterKeyColum(0)

        self._populate_region_combo()
        self._populate_departement_combo()
        self._populate_epci_combo()

        self.comboBox_region.currentIndexChanged.connect(self._on_region_changed)
        self.comboBox_departement.currentIndexChanged.connect(
            self._on_departement_changed
        )
        self.comboBox_epci.currentIndexChanged.connect(self._on_epci_changed)

    def current_selection(self) -> SituationSelection:
        """Return the current selection without emitting the signal."""
        return SituationSelection(
            code_reg=self.comboBox_region.currentData(),
            code_dep=self.comboBox_departement.currentData(),
            code_epci=self.comboBox_epci.currentData(),
        )

    def _populate_region_combo(self) -> None:
        _fill_combo_model(self._region_model, self._regions)

    def _populate_departement_combo(self) -> None:
        _fill_combo_model(self._departement_model, self._filtered_departements())

    def _setup_epci_combobox(self) -> None:
        self.comboBox_epci = CompleterComboBox(self)
        self.comboBox_epci.setObjectName("comboBox_epci")
        self.horizontalLayout_epci_combobox.addWidget(self.comboBox_epci)

    def _populate_epci_combo(self) -> None:
        _fill_combo_model(self._epci_model, self._filtered_epcis())
        self.comboBox_epci.filter_model.setFilterFixedString("")

    def _filtered_departements(self) -> list[Departement]:
        code_reg = self.comboBox_region.currentData()
        if not code_reg:
            return self._departements
        return [d for d in self._departements if d.code_reg == code_reg]

    def _filtered_epcis(self) -> list[Epci]:
        code_reg = self.comboBox_region.currentData()
        code_dep = self.comboBox_departement.currentData()
        items: list[Epci] = self._epcis
        if code_reg:
            items = [e for e in items if e.code_reg == code_reg]
        if code_dep:
            items = [e for e in items if e.code_dep == code_dep]
        return items

    def _on_region_changed(self, _index: int) -> None:
        with _blocked(self.comboBox_departement), _blocked(self.comboBox_epci):
            self._populate_departement_combo()
            self._populate_epci_combo()
        self._emit_selection()

    def _on_departement_changed(self, _index: int) -> None:
        with _blocked(self.comboBox_epci):
            self._populate_epci_combo()
        self._emit_selection()

    def _on_epci_changed(self, _index: int) -> None:
        self._emit_selection()

    def _emit_selection(self) -> None:
        self.selection_changed.emit(self.current_selection())


@contextmanager
def _blocked(combo: QComboBox):
    """Temporarily block signals on ``combo`` while a model is rebuilt."""
    previous = combo.blockSignals(True)
    try:
        yield
    finally:
        combo.blockSignals(previous)
