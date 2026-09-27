from pathlib import Path


# ---------------------------------------------------------
# Project structure
# ---------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[3]

NB4_OUTPUT_DIR = (
    PROJECT_DIR
    / "outputs"
    / "notebook4_programme_review"
)

GEOGRAPHY_DIR = PROJECT_DIR / "geography"

DASHBOARD_DIR = PROJECT_DIR / "dashboard"

SPEC_DIR = (
    DASHBOARD_DIR
    / "specification"
)


# ---------------------------------------------------------
# Validated dashboard geography
# ---------------------------------------------------------

DASHBOARD_GEOJSON_PATH = (
    GEOGRAPHY_DIR
    / "ethiopia_admin1_dashboard.geojson"
)

REGION_CROSSWALK_PATH = (
    GEOGRAPHY_DIR
    / "region_name_crosswalk.csv"
)


# ---------------------------------------------------------
# Dashboard specification
# ---------------------------------------------------------

SOURCE_VISUAL_SPEC_PATH = (
    SPEC_DIR
    / "source_to_visual_mapping.csv"
)

EQUITY_REGISTRY_PATH = (
    SPEC_DIR
    / "equity_indicator_registry.csv"
)

REGIONAL_REGISTRY_PATH = (
    SPEC_DIR
    / "regional_indicator_registry.csv"
)
