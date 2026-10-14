import argparse
import logging
from pathlib import Path
from .config import load

def main():
    parser = argparse.ArgumentParser(description="Online Retail II data analysis")
    parser.add_argument("command", nargs="?", default="run", choices=["download", "prepare", "run"])
    args = parser.parse_args()
    config = load()
    out = Path(config["output_dir"]); out.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.StreamHandler(), logging.FileHandler(out / "pipeline.log", encoding="utf-8")])
    try:
        if args.command == "download":
            from .prepare import download
            download(config)
        elif args.command == "prepare":
            from .prepare import prepare
            prepare(config)
        else:
            from .pipeline import run
            run(config)
    except Exception:
        logging.exception("Pipeline failed")
        raise
