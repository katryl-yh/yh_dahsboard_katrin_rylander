from pathlib import Path

# Project & data paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = PROJECT_ROOT / "data" / "resultat_kurser"

# Filenames & sheets
EXCEL_RESULTS_FILE = "resultat-2025-for-kurser-inom-yh.xlsx"
EXCEL_RESULTS_SHEET = "Lista ansökningar"

EXCEL_APPS_FILE = "inkomna-ansokningar-2025-for-kurser.xlsx"
EXCEL_APPS_SHEET = "Lista ansökningar"

# Columns & prefixes
REQUIRED_COLUMNS = {"Län", "Beslut", "Utbildningsområde"}
KEY_COL = "Diarienummer"
SOKT_PREFIX = "Sökt antal platser"

COL_TOTAL_SOKTA = "Totalt antal sökta platser"
COL_TOTAL_BEVILJADE_PLATSER = "Totalt antal beviljade platser"