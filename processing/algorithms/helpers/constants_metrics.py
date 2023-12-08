FAST_MODE_EXCLUSION_METRICS: list[str] = ["patch metrics"]

TYPES_OF_METRICS: dict[str, list[str]] = {
    "basic metrics": [
        "N-total",
        "N-valid",
        "pN-valid",
        "NC-valid",
        "pNC-valid",
    ],
    "value metrics": [
        "Nclass",
        "Central",
        "pCentral",
        "Majority",
    ],
    "couple metrics": [
        "NC-hete",
        "pNC-hete",
    ],
    "diversity metrics": [
        "HET",
        "HET-frag",
        "SHDI",
        "SHEI",
    ],
    "patch metrics": [
        "LPI",
        "MPS",
        "NP",
    ],
    "quantitative metrics": [
        "average",
        "sum",
        "standard_deviation",
        "minimum",
        "maximum",
        "vCentral",
    ],
}


TYPES_OF_METRICS_SIMPLE: dict[str, list[str]] = {
    "value metrics": [
        "NV_",
        "pNV_",
    ],
    "patch metrics": [
        "LPI-class_",
        "MPS-class_",
        "NP-class_",
    ],
}

TYPES_OF_METRICS_CROSS: dict[str, list[str]] = {
    "couple metrics": [
        "NC_",
        "pNC_",
    ],
}
