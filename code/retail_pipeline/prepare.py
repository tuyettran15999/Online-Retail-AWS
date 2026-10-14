"""Stream the two original workbook sheets to normalized CSV files."""
import csv
import hashlib
import os
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile
import openpyxl

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
COLUMNS = ["invoice", "stockcode", "description", "quantity", "invoicedate", "price", "customer_id", "country"]
ALIASES = {"invoice": "invoice", "invoiceno": "invoice", "stockcode": "stockcode", "description": "description", "quantity": "quantity", "invoicedate": "invoicedate", "price": "price", "unitprice": "price", "customerid": "customer_id", "country": "country"}

def download(config):
    target = Path(config["source_workbook"])
    target.parent.mkdir(parents=True, exist_ok=True)
    archive = target.parent / "download.zip"
    try:
        with urlopen(URL, timeout=120) as response, archive.open("wb") as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        with ZipFile(archive) as z:
            with z.open("online_retail_II.xlsx") as source, target.with_suffix(".tmp").open("wb") as out:
                while chunk := source.read(1024 * 1024):
                    out.write(chunk)
        os.replace(target.with_suffix(".tmp"), target)
    finally:
        archive.unlink(missing_ok=True)

def prepare(config):
    source = Path(config["source_workbook"])
    workbook = openpyxl.load_workbook(source, read_only=True, data_only=True)
    folder = Path(config["raw_dir"])
    folder.mkdir(parents=True, exist_ok=True)
    counts = {}
    try:
        for index, sheet in enumerate(workbook.worksheets):
            name = ["Year_2009-2010_online_retail_II.csv", "Year_2010-2011_online_retail_II.csv"][index]
            rows = sheet.iter_rows(values_only=True)
            header = next(rows)
            normalized = [ALIASES.get(str(h).replace(" ", "").lower()) for h in header]
            if normalized != COLUMNS:
                raise ValueError(f"Unexpected workbook schema: {header}")
            temp = folder / (name + ".tmp")
            count = 0
            with temp.open("w", newline="", encoding="utf-8") as out:
                writer = csv.writer(out); writer.writerow(COLUMNS)
                for count, row in enumerate(rows, 1):
                    values = list(row)
                    if hasattr(values[4], "isoformat"):
                        values[4] = values[4].isoformat(sep=" ")
                    writer.writerow(values)
            os.replace(temp, folder / name)
            counts[name] = count
            print(f"Prepared {name}: {count:,} rows", flush=True)
    finally:
        workbook.close()
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    lines = ["Online Retail II source manifest", f"Download URL: {URL}", f"Workbook SHA-256: {checksum}"]
    lines += [f"{name}: {count:,} rows" for name, count in counts.items()]
    (source.parent / "source_manifest.txt").write_text("\n".join(lines) + "\n")
    return counts
