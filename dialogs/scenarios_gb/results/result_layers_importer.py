from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from qgis.core import (
    Qgis,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsProject,
    QgsRasterLayer,
)
from qgis.utils import iface

from .constants import (
    RESULT_EA_GROUP_LABEL,
    RESULT_EA_RASTER_PREFIX,
    RESULT_EXTERNE_FOLDER_NAME,
    RESULT_EXTERNE_GROUP_LABEL,
    RESULT_INITIAL_FOLDER_NAME,
    RESULT_INITIAL_GROUP_LABEL,
    RESULT_LAYER_RASTER_EXTENSIONS,
    RESULT_LAYER_RASTER_PREFIXES,
    RESULT_LAYER_SUBGROUPS,
    RESULT_LAYERS_ROOT_GROUP_NAME,
    ResultLayerSubgroup,
)


class SelectableFolderKind(Enum):
    """Kind of result folder available for layer import."""

    SCENARIO = "scenario"
    EXTERNE = "externe"
    INITIAL = "initial"
    EA = "ea"


_SPECIAL_FOLDER_BY_NAME: dict[str, tuple[str, SelectableFolderKind]] = {
    RESULT_EXTERNE_FOLDER_NAME: (
        RESULT_EXTERNE_GROUP_LABEL,
        SelectableFolderKind.EXTERNE,
    ),
    RESULT_INITIAL_FOLDER_NAME: (
        RESULT_INITIAL_GROUP_LABEL,
        SelectableFolderKind.INITIAL,
    ),
}


@dataclass(frozen=True)
class SelectableFolder:
    """A loadable result folder or virtual EA group within an exploitation directory."""

    label: str
    kind: SelectableFolderKind
    path: Path


@dataclass(frozen=True)
class SelectableLayer:
    """A loadable raster within a result folder."""

    label: str
    path: Path
    is_loaded: bool
    subgroup: ResultLayerSubgroup | None = None


@dataclass(frozen=True)
class SelectableLayerGroup:
    """A subgroup of loadable rasters within a result folder.

    A None label means the layers are placed directly under the folder.
    """

    label: str | None
    layers: list[SelectableLayer]


def get_or_create_group(parent, name: str) -> QgsLayerTreeGroup:
    """Return an existing layer tree group or create it under parent."""
    existing_group: QgsLayerTreeGroup | None = parent.findGroup(name)
    if existing_group is not None:
        return existing_group
    return parent.addGroup(name)


def get_or_create_ordered_group(
    parent: QgsLayerTreeGroup, name: str, ordered_labels: list[str]
) -> QgsLayerTreeGroup:
    """Return an existing group or create it at its canonical position.

    Unlike :func:`get_or_create_group`, which always appends new groups at the
    end, this inserts a new group so siblings follow ``ordered_labels``. This
    keeps incremental imports (e.g. loading ``scenario_0`` after other folders)
    in the same order as a single-pass import. Labels absent from
    ``ordered_labels`` are appended at the end.
    """
    existing_group: QgsLayerTreeGroup | None = parent.findGroup(name)
    if existing_group is not None:
        return existing_group

    if name not in ordered_labels:
        return parent.addGroup(name)

    target_rank = ordered_labels.index(name)
    insert_index = len(parent.children())
    for index, child in enumerate(parent.children()):
        if (
            isinstance(child, QgsLayerTreeGroup)
            and child.name() in ordered_labels
            and ordered_labels.index(child.name()) > target_rank
        ):
            insert_index = index
            break
    return parent.insertGroup(insert_index, name)


def matches_prefixes(stem: str, prefixes: list[str]) -> bool:
    """Check if the stem matches any of the prefixes."""
    return any(stem.startswith(prefix) for prefix in prefixes)


def normalize_source_path(source: Path | str) -> str:
    """Return a resolved, comparable source path string."""
    return str(Path(source).resolve())


def layer_resolved_source(layer: QgsMapLayer | None) -> str | None:
    """Return the resolved source path of a map layer, if available."""
    if layer is None:
        return None
    return normalize_source_path(layer.source())


def subgroup_label(subgroup: ResultLayerSubgroup | None) -> str | None:
    """Return the display label for a subgroup config, if any."""
    return subgroup.label if subgroup is not None else None


def get_result_layer_subgroup(stem: str) -> ResultLayerSubgroup | None:
    """Return the subgroup config for a raster stem, or ``None`` if unmatched.

    Matching uses ``startswith`` to mirror :func:`matches_prefixes`. Order in
    ``RESULT_LAYER_SUBGROUPS`` is significant: a more specific keyword (e.g.
    ``grain_bocager_4classes``) must precede a prefix of it (``grain_bocager``).
    """
    for subgroup in RESULT_LAYER_SUBGROUPS:
        if stem.startswith(subgroup.keyword):
            return subgroup
    return None


def get_layer_subgroup_label(stem: str) -> str | None:
    """Return the subgroup label for a raster stem, or ``None`` if unmatched."""
    return subgroup_label(get_result_layer_subgroup(stem))


def iter_loadable_rasters(
    folder: Path,
    prefixes: list[str],
    allowed_paths: set[Path] | None = None,
) -> Iterator[Path]:
    """Yield loadable raster paths from a folder in sorted order."""
    if not folder.is_dir():
        return

    for file_path in sorted(folder.iterdir(), key=lambda path: path.name):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in RESULT_LAYER_RASTER_EXTENSIONS:
            continue
        if not matches_prefixes(file_path.stem, prefixes):
            continue
        if allowed_paths is not None and file_path.resolve() not in allowed_paths:
            continue
        yield file_path


def has_ea_rasters(exploitation_folder: Path) -> bool:
    """Check if the exploitation folder contains EA rasters."""
    return any(iter_loadable_rasters(exploitation_folder, [RESULT_EA_RASTER_PREFIX]))


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
        special_folder = _SPECIAL_FOLDER_BY_NAME.get(folder_name)
        if special_folder is not None:
            label, kind = special_folder
            selectable_folder = SelectableFolder(label=label, kind=kind, path=entry)
            if kind is SelectableFolderKind.EXTERNE:
                externe_folder = selectable_folder
            else:
                initial_folder = selectable_folder
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


def folder_raster_prefixes(folder: SelectableFolder) -> list[str]:
    """Return raster filename prefixes for the given folder kind."""
    if folder.kind == SelectableFolderKind.EA:
        return [RESULT_EA_RASTER_PREFIX]
    return RESULT_LAYER_RASTER_PREFIXES


def list_folder_rasters(folder: SelectableFolder) -> list[Path]:
    """List loadable raster paths for a selectable folder in sorted order."""
    return list(iter_loadable_rasters(folder.path, folder_raster_prefixes(folder)))


def resolve_folder_group(
    id_exploitation: str, folder_label: str
) -> QgsLayerTreeGroup | None:
    """Resolve the QGIS layer tree group for a result folder, if it exists."""
    layer_tree = QgsProject.instance().layerTreeRoot()
    root_group = layer_tree.findGroup(RESULT_LAYERS_ROOT_GROUP_NAME)
    if root_group is None:
        return None
    exploitation_group = root_group.findGroup(id_exploitation)
    if exploitation_group is None:
        return None
    return exploitation_group.findGroup(folder_label)


def collect_group_layer_sources(group: QgsLayerTreeGroup) -> set[str]:
    """Recursively collect resolved source paths of rasters within a group."""
    sources: set[str] = set()
    for child in group.children():
        if isinstance(child, QgsLayerTreeLayer):
            source = layer_resolved_source(child.layer())
            if source is not None:
                sources.add(source)
        elif isinstance(child, QgsLayerTreeGroup):
            sources |= collect_group_layer_sources(child)
    return sources


def get_loaded_raster_sources(id_exploitation: str, folder_label: str) -> set[str]:
    """Return resolved source paths of rasters already loaded in the target group."""
    folder_group = resolve_folder_group(id_exploitation, folder_label)
    if folder_group is None:
        return set()
    return collect_group_layer_sources(folder_group)


def build_selectable_layers(
    id_exploitation: str, folder: SelectableFolder
) -> list[SelectableLayer]:
    """Build selectable layer entries with loaded-state for a folder."""
    loaded_sources: set[str] = get_loaded_raster_sources(id_exploitation, folder.label)
    selectable_layers: list[SelectableLayer] = []
    for raster_path in list_folder_rasters(folder):
        subgroup = get_result_layer_subgroup(raster_path.stem)
        selectable_layers.append(
            SelectableLayer(
                label=raster_path.stem,
                path=raster_path,
                is_loaded=normalize_source_path(raster_path) in loaded_sources,
                subgroup=subgroup,
            )
        )
    return selectable_layers


def build_selectable_layer_groups(
    id_exploitation: str, folder: SelectableFolder
) -> list[SelectableLayerGroup]:
    """Build subgroups of selectable layers for a folder, in display order.

    Layers are grouped by their subgroup label. Subgroups are ordered following
    ``RESULT_LAYER_SUBGROUPS`` and any unmatched layers are returned last in a
    group with a ``None`` label (placed directly under the folder).
    """
    layers = build_selectable_layers(id_exploitation, folder)
    if not layers:
        return []

    grouped: dict[str | None, list[SelectableLayer]] = {}
    for layer in layers:
        grouped.setdefault(subgroup_label(layer.subgroup), []).append(layer)

    ordered_groups: list[SelectableLayerGroup] = []
    for subgroup in RESULT_LAYER_SUBGROUPS:
        subgroup_layers = grouped.pop(subgroup.label, None)
        if subgroup_layers:
            ordered_groups.append(
                SelectableLayerGroup(label=subgroup.label, layers=subgroup_layers)
            )

    unmatched_layers = grouped.pop(None, None)
    if unmatched_layers:
        ordered_groups.append(SelectableLayerGroup(label=None, layers=unmatched_layers))

    # Any remaining labels not declared in RESULT_LAYER_SUBGROUPS.
    for remaining_label, remaining_layers in grouped.items():
        ordered_groups.append(
            SelectableLayerGroup(label=remaining_label, layers=remaining_layers)
        )

    return ordered_groups


def prepare_exploitation_group(
    id_exploitation: str,
) -> tuple[QgsProject, QgsLayerTreeGroup]:
    """Create or resolve the nested QGIS groups for a result import."""
    qgs_project = QgsProject.instance()
    layer_tree = qgs_project.layerTreeRoot()
    root_group = get_or_create_group(layer_tree, RESULT_LAYERS_ROOT_GROUP_NAME)
    root_group.setExpanded(False)
    exploitation_group = get_or_create_group(root_group, id_exploitation)
    exploitation_group.setExpanded(False)
    return qgs_project, exploitation_group


def resolve_exploitation_folder(folder: SelectableFolder) -> Path:
    """Return the exploitation directory a selectable folder belongs to.

    For the virtual ``EA`` group the path is the exploitation folder itself;
    for every other kind the rasters live in a direct subfolder of it.
    """
    if folder.kind is SelectableFolderKind.EA:
        return folder.path
    return folder.path.parent


def import_result_folders(
    id_exploitation: str,
    folder_imports: list[tuple[SelectableFolder, set[Path] | None]],
) -> None:
    """Import rasters for each folder, optionally restricted to allowed paths."""
    if not folder_imports:
        return

    qgs_project, exploitation_group = prepare_exploitation_group(id_exploitation)

    exploitation_folder = resolve_exploitation_folder(folder_imports[0][0])
    ordered_labels = [
        folder.label for folder in get_selectable_folders(exploitation_folder)
    ]

    for selectable_folder, allowed_paths in folder_imports:
        if allowed_paths is not None and not allowed_paths:
            continue
        target_group = get_or_create_ordered_group(
            exploitation_group, selectable_folder.label, ordered_labels
        )
        target_group.setExpanded(False)
        load_rasters_into_group(
            folder=selectable_folder.path,
            group=target_group,
            prefixes=folder_raster_prefixes(selectable_folder),
            qgs_project=qgs_project,
            allowed_paths=allowed_paths,
        )


def import_selected_result_layers(
    id_exploitation: str,
    selections: list[tuple[SelectableFolder, list[Path]]],
) -> None:
    """Import individually selected result rasters into nested QGIS layer groups."""
    import_result_folders(
        id_exploitation,
        [(folder, {path.resolve() for path in paths}) for folder, paths in selections],
    )


def layer_exists_in_group(group: QgsLayerTreeGroup, file_path: Path) -> bool:
    """Check if a layer exists in a QGIS group."""
    normalized_path = normalize_source_path(file_path)
    for child in group.children():
        if isinstance(child, QgsLayerTreeLayer):
            if layer_resolved_source(child.layer()) == normalized_path:
                return True
    return False


def load_rasters_into_group(
    folder: Path,
    group: QgsLayerTreeGroup,
    prefixes: list[str],
    qgs_project: QgsProject,
    allowed_paths: set[Path] | None = None,
) -> None:
    """Load rasters into a QGIS group."""
    for file_path in iter_loadable_rasters(folder, prefixes, allowed_paths):
        target_group = group
        layer_subgroup_label = get_layer_subgroup_label(file_path.stem)
        if layer_subgroup_label is not None:
            target_group = get_or_create_group(group, layer_subgroup_label)
            target_group.setExpanded(False)

        if layer_exists_in_group(target_group, file_path):
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
        layer_node = target_group.addLayer(raster_layer)
        layer_node.setExpanded(False)
