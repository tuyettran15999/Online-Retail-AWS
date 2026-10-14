"""Compatibility entry point; the main analysis script is code/run_pipeline.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "code"))
from retail_pipeline.cli import main

if __name__ == "__main__":
    main()
