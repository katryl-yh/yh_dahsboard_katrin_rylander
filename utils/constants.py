from pathlib import Path

# Project & data paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = PROJECT_ROOT / "data" / "resultat_kurser"

# Filenames & sheets
EXCEL_RESULTS_FILE = "resultat-2025-for-kurser-inom-yh.xlsx"
EXCEL_RESULTS_SHEET = "Lista ansökningar"

EXCEL_APPS_FILE = "inkomna-ansokningar-2025-for-kurser.xlsx"
EXCEL_APPS_SHEET = "Lista ansökningar"

# Data column names
COL_LAN = "Län"
COL_BESLUT = "Beslut"
COL_ANORDNARE = "Anordnare namn"
COL_CREDITS = "YH-poäng"
COL_EDUCATION_AREA = "Utbildningsområde"

# Decision values
BESLUT_BEVILJAD = "Beviljad"
BESLUT_AVSLAG = "Avslag"

# Columns & prefixes
REQUIRED_COLUMNS = {"Län", "Beslut", "Utbildningsområde"}
KEY_COL = "Diarienummer"
SOKT_PREFIX = "Sökt antal platser"

COL_TOTAL_SOKTA = "Totalt antal sökta platser"
COL_TOTAL_BEVILJADE_PLATSER = "Totalt antal beviljade platser"

# Color constants
GRAY_1 = "#CCCCCC"
GRAY_2 = "#657072"
GRAY_3 = "#4A606C"
BLUE_1 = "#1f77b4"
BLUE_11 = "#0284c7"
GRAY_11 = "#d1d5db"
GRAY_12 = "#989898"
GRAY_13 = "#4A606C"