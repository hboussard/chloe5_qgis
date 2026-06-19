from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from qgis.core import (
    Qgis,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsProject,
    QgsRasterLayer,
)
from qgis.utils import iface

from ....helpers.helpers import get_or_create_group
from .constants import (
    RESULT_EA_GROUP_LABEL,
    RESULT_EA_RASTER_PREFIX,
    RESULT_EXTERNE_FOLDER_NAME,
    RESULT_EXTERNE_GROUP_LABEL,
    RESULT_INITIAL_FOLDER_NAME,
    RESULT_INITIAL_GROUP_LABEL,
    RESULT_LAYER_RASTER_EXTENSIONS,
    RESULT_LAYER_RASTER_PREFIXES,
    RESULT_LAYERS_ROOT_GROUP_NAME,
)


class SelectableFolderKind(Enum):
    """Kind of result folder available for layer import."""

    SCENARIO = "scenario"
    EXTERNE = "externe"
    INITIAL = "initial"
    EA = "ea"


@dataclass(frozen=True)
class SelectableFolder:
    """A loadable result folder or virtual EA group within an exploitation directory."""

    label: str
    kind: SelectableFolderKind
    path: Path


def get_selectable_folders(exploitation_folder: Path) -> list[SelectableFolder]:
    """List subfolders and the EA group available for import in load order."""
    if not exploitation_folder.is_dir():
        return []

    ordered_folders: list[SelectableFolder] = []
    externe_folder: SelectableFolder | None = None
    initial_folder: SelectableFolder | None = None

    for entry in exploitation_folder.iterdir():
        if not entry.is_dir():
            continue
        folder_name = entry.name.lower()
        if folder_name == RESULT_EXTERNE_FOLDER_NAME:
            externe_folder = SelectableFolder(
                label=RESULT_EXTERNE_GROUP_LABEL,
                kind=SelectableFolderKind.EXTERNE,
                path=entry,
            )
        elif folder_name == RESULT_INITIAL_FOLDER_NAME:
            initial_folder = SelectableFolder(
                label=RESULT_INITIAL_GROUP_LABEL,
                kind=SelectableFolderKind.INITIAL,
                path=entry,
            )
        else:
            ordered_folders.append(
                SelectableFolder(
                    label=entry.name,
                    kind=SelectableFolderKind.SCENARIO,
                    path=entry,
                )
            )
    # sort the folders by label
    # TODO : sort by properties files timestamp instead of label ?
    ordered_folders.sort(key=lambda folder: folder.label)
    if externe_folder is not None:
        ordered_folders.append(externe_folder)
    if initial_folder is not None:
        ordered_folders.append(initial_folder)
    if has_ea_rasters(exploitation_folder):
        ordered_folders.append(
            SelectableFolder(
                label=RESULT_EA_GROUP_LABEL,
                kind=SelectableFolderKind.EA,
                path=exploitation_folder,
            )
        )

    return ordered_folders


def import_result_layers(
    id_exploitation: str,
    selected_folders: list[SelectableFolder],
) -> None:
    """Import selected result rasters into nested QGIS layer groups."""
    if not selected_folders:
        return

    qgs_project = QgsProject.instance()
    layer_tree = qgs_project.layerTreeRoot()
    root_group = get_or_create_group(layer_tree, RESULT_LAYERS_ROOT_GROUP_NAME)
    root_group.setExpanded(False)
    exploitation_group = get_or_create_group(root_group, id_exploitation)
    exploitation_group.setExpanded(False)

    for selectable_folder in selected_folders:
        target_group = get_or_create_group(exploitation_group, selectable_folder.label)
        target_group.setExpanded(False)
        if selectable_folder.kind == SelectableFolderKind.EA:
            load_rasters_into_group(
                folder=selectable_folder.path,
                group=target_group,
                prefixes=[RESULT_EA_RASTER_PREFIX],
                qgs_project=qgs_project,
            )
        else:
            load_rasters_into_group(
                folder=selectable_folder.path,
                group=target_group,
                prefixes=RESULT_LAYER_RASTER_PREFIXES,
                qgs_project=qgs_project,
            )


def has_ea_rasters(exploitation_folder: Path) -> bool:
    """Check if the exploitation folder contains EA rasters."""
    for file_path in exploitation_folder.iterdir():
        if (
            file_path.is_file()
            and file_path.suffix.lower() in RESULT_LAYER_RASTER_EXTENSIONS
            and file_path.stem.startswith(RESULT_EA_RASTER_PREFIX)
        ):
            return True
    return False


def matches_prefixes(stem: str, prefixes: list[str]) -> bool:
    """Check if the stem matches any of the prefixes."""
    return any(stem.startswith(prefix) for prefix in prefixes)


def layer_exists_in_group(group: QgsLayerTreeGroup, file_path: Path) -> bool:
    """Check if a layer exists in a QGIS group."""
    normalized_path = str(file_path.resolve())
    for child in group.children():
        if isinstance(child, QgsLayerTreeLayer):
            layer = child.layer()
            if (
                layer is not None
                and str(Path(layer.source()).resolve()) == normalized_path
            ):
                return True
    return False


def load_rasters_into_group(
    folder: Path,
    group: QgsLayerTreeGroup,
    prefixes: list[str],
    qgs_project: QgsProject,
) -> None:
    """Load rasters into a QGIS group."""
    if not folder.is_dir():
        return

    for file_path in sorted(folder.iterdir(), key=lambda path: path.name):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in RESULT_LAYER_RASTER_EXTENSIONS:
            continue
        if not matches_prefixes(file_path.stem, prefixes):
            continue
        if layer_exists_in_group(group, file_path):
            continue

        raster_layer = QgsRasterLayer(str(file_path), file_path.stem)
        if not raster_layer.isValid():
            iface.messageBar().pushMessage(
                "Erreur",
                f"Impossible de charger le raster {file_path}",
                level=Qgis.Critical,
            )
            continue
        qgs_project.addMapLayer(raster_layer, False)
        layer_node = group.addLayer(raster_layer)
        layer_node.setExpanded(False)
