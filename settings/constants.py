SETTINGS_JAVA_PATH: str = "chloe_qgis/javaPath"

SETTINGS_MEMORY_HEAP_SIZE: str = "chloe_qgis/memoryHeapSize"
DEFAULT_MEMORY_HEAP_SIZE: int = 4


SETTINGS_GEOGRAPHIC_CONTEXT: str = "chloe_qgis/geographicContext"
DEFAULT_GEOGRAPHIC_CONTEXT: str = "france"

AVAILABLE_GEOGRAPHIC_CONTEXTS: dict[str, str] = {
    "france": "France",
    "ireland": "Ireland",
    "great_britain": "Great-Britain",
    "new_zealand": "New-Zealand",
    "chile": "Chile",
}
