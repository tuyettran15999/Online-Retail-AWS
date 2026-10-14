"""Project paths. Edit this file to customize local input/output locations."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports"
DATABASE = PROCESSED_DIR / "retail.duckdb"
SOURCE_WORKBOOK = RAW_DIR / "online_retail_II.xlsx"
