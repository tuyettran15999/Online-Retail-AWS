"""Expose the Python settings to pipeline modules; no JSON configuration needed."""
from .settings import ROOT, RAW_DIR, PROCESSED_DIR, REPORTS_DIR, DATABASE, SOURCE_WORKBOOK

def load():
    return {
        "database": str(DATABASE),
        "output_dir": str(REPORTS_DIR),
        "processed_dir": str(PROCESSED_DIR),
        "full_glob": str(RAW_DIR / "Year_*_online_retail_II.csv"),
        "source_workbook": str(SOURCE_WORKBOOK),
        "raw_dir": str(RAW_DIR),
    }
