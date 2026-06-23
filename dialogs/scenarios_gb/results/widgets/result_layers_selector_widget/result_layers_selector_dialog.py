# -*- coding: utf-8 -*-

from pathlib import Path

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTreeView,
    QVBoxLayout,
)

from ...result_layers_importer import (
    SelectableFolder,
    SelectableLayer,
    SelectableLayerGroup,
    build_selectable_layer_groups,
)
from ......helpers.helpers import tr

_FOLDER_ROLE = Qt.UserRole
_LAYER_PATH_ROLE = Qt.UserRole + 1
_LOADED_STATUS_LABEL = "Déjà chargé"


class ResultLayersSelectorDialog(QDialog):
    """Tree dialog to select result rasters grouped by folder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._id_exploitation = ""
        self._folders: list[SelectableFolder] = []
        self._tree_model = QStandardItemModel(self)
        self._return_values: list[tuple[SelectableFolder, list[Path]]] = []
        self._updating_checks = False

        self._init_gui()
        self._tree_model.itemChanged.connect(self._on_item_changed)

    def _init_gui(self) -> None:
        main_layout = QVBoxLayout(self)

        self._tree_view = QTreeView(self)
        self._tree_view.setModel(self._tree_model)
        self._tree_view.setHeaderHidden(False)
        self._tree_view.setUniformRowHeights(True)
        self._tree_view.setExpandsOnDoubleClick(True)
        main_layout.addWidget(self._tree_view)

        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)

        btn_all = QPushButton(tr("All"))
        btn_nothing = QPushButton(tr("Nothing"))
        btn_submit = QPushButton(tr("Ok"))

        buttons_layout.addWidget(btn_all)
        buttons_layout.addWidget(btn_nothing)
        buttons_layout.addWidget(btn_submit)

        btn_all.clicked.connect(self._select_all_values)
        btn_nothing.clicked.connect(self._unselect_all_values)
        btn_submit.clicked.connect(self._submit)

        self._tree_model.setHorizontalHeaderLabels([tr("Nom")])
        header = self._tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)

    def set_data(self, id_exploitation: str, folders: list[SelectableFolder]) -> None:
        """Refresh dialog content for the given exploitation and folders."""
        self._id_exploitation = id_exploitation
        self._folders = folders
        self._return_values = []
        self._populate_tree_model()

    def _populate_tree_model(self) -> None:
        self._updating_checks = True
        try:
            self._tree_model.clear()
            self._tree_model.setHorizontalHeaderLabels([tr("Nom")])

            for folder in self._folders:
                layer_groups = build_selectable_layer_groups(
                    self._id_exploitation, folder
                )
                if not layer_groups:
                    continue

                folder_item = self._create_group_item(folder.label)
                folder_item.setData(folder, _FOLDER_ROLE)

                for layer_group in layer_groups:
                    self._append_layer_group(folder_item, layer_group)

                self._refresh_group_state(folder_item)
                self._tree_model.appendRow(folder_item)
        finally:
            self._updating_checks = False

    def _create_group_item(self, label: str) -> QStandardItem:
        group_item = QStandardItem(label)
        group_item.setCheckable(True)
        group_item.setTristate(True)
        group_item.setEditable(False)
        return group_item

    def _append_layer_group(
        self, parent_item: QStandardItem, layer_group: SelectableLayerGroup
    ) -> None:
        # Layers without a subgroup label are placed directly under the folder.
        if layer_group.label is None:
            for selectable_layer in layer_group.layers:
                parent_item.appendRow(self._create_layer_item(selectable_layer))
            return

        subgroup_item = self._create_group_item(layer_group.label)
        for selectable_layer in layer_group.layers:
            subgroup_item.appendRow(self._create_layer_item(selectable_layer))
        parent_item.appendRow(subgroup_item)

    def _create_layer_item(self, selectable_layer: SelectableLayer) -> QStandardItem:
        label = selectable_layer.label
        if selectable_layer.is_loaded:
            label = f"({tr(_LOADED_STATUS_LABEL)}) {label}"

        layer_item = QStandardItem(label)
        layer_item.setData(selectable_layer.path, _LAYER_PATH_ROLE)
        layer_item.setCheckable(True)
        layer_item.setEditable(False)

        if selectable_layer.is_loaded:
            layer_item.setCheckState(Qt.Unchecked)
            layer_item.setFlags(layer_item.flags() & ~Qt.ItemIsEnabled)
        elif (
            selectable_layer.subgroup is not None
            and not selectable_layer.subgroup.checked_by_default
        ):
            layer_item.setCheckState(Qt.Unchecked)
        else:
            layer_item.setCheckState(Qt.Checked)

        return layer_item

    def _refresh_group_state(self, group_item: QStandardItem) -> None:
        """Recompute a group's check state bottom-up from its descendants."""
        enabled_states: list[Qt.CheckState] = []
        for row_index in range(group_item.rowCount()):
            child = group_item.child(row_index, 0)
            if child is None:
                continue
            if child.hasChildren():
                self._refresh_group_state(child)
            if child.flags() & Qt.ItemIsEnabled:
                enabled_states.append(child.checkState())

        if not enabled_states:
            group_item.setCheckState(Qt.Unchecked)
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsEnabled)
            return

        if all(state == Qt.Checked for state in enabled_states):
            group_item.setCheckState(Qt.Checked)
        elif all(state == Qt.Unchecked for state in enabled_states):
            group_item.setCheckState(Qt.Unchecked)
        else:
            group_item.setCheckState(Qt.PartiallyChecked)

    def _set_leaves_check_state(
        self, group_item: QStandardItem, state: Qt.CheckState
    ) -> None:
        """Apply a check state to every enabled leaf under a group."""
        for row_index in range(group_item.rowCount()):
            child = group_item.child(row_index, 0)
            if child is None:
                continue
            if child.hasChildren():
                self._set_leaves_check_state(child, state)
            elif child.flags() & Qt.ItemIsEnabled:
                child.setCheckState(state)

    def _collect_checked_paths(self, group_item: QStandardItem) -> list[Path]:
        """Collect paths of every enabled, checked leaf under a group."""
        paths: list[Path] = []
        for row_index in range(group_item.rowCount()):
            child = group_item.child(row_index, 0)
            if child is None:
                continue
            if child.hasChildren():
                paths.extend(self._collect_checked_paths(child))
                continue
            if not child.flags() & Qt.ItemIsEnabled:
                continue
            if child.checkState() != Qt.Checked:
                continue
            layer_path = child.data(_LAYER_PATH_ROLE)
            if isinstance(layer_path, Path):
                paths.append(layer_path)
        return paths

    def _iter_folder_items(self):
        for row_index in range(self._tree_model.rowCount()):
            folder_item = self._tree_model.item(row_index, 0)
            if folder_item is not None:
                yield folder_item

    def _on_item_changed(self, item: QStandardItem) -> None:
        if self._updating_checks:
            return

        self._updating_checks = True
        try:
            if item.hasChildren():
                self._set_leaves_check_state(item, item.checkState())
            for folder_item in self._iter_folder_items():
                self._refresh_group_state(folder_item)
        finally:
            self._updating_checks = False

    def _set_all_values(self, state: Qt.CheckState) -> None:
        self._updating_checks = True
        try:
            for folder_item in self._iter_folder_items():
                if not folder_item.flags() & Qt.ItemIsEnabled:
                    continue
                self._set_leaves_check_state(folder_item, state)
                self._refresh_group_state(folder_item)
        finally:
            self._updating_checks = False

    def _select_all_values(self) -> None:
        self._set_all_values(Qt.Checked)

    def _unselect_all_values(self) -> None:
        self._set_all_values(Qt.Unchecked)

    def _submit(self) -> None:
        selections: list[tuple[SelectableFolder, list[Path]]] = []

        for folder_item in self._iter_folder_items():
            folder: SelectableFolder | None = folder_item.data(_FOLDER_ROLE)
            if folder is None:
                continue

            selected_paths = self._collect_checked_paths(folder_item)
            if selected_paths:
                selections.append((folder, selected_paths))

        self._return_values = selections
        self.accept()

    def run(
        self,
        id_exploitation: str,
        folders: list[SelectableFolder],
    ) -> list[tuple[SelectableFolder, list[Path]]]:
        self.set_data(id_exploitation, folders)
        self.setWindowTitle(tr("Select result layers"))
        self.resize(520, 420)
        self.exec()
        return self._return_values
