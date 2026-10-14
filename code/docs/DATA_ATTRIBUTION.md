# Data provenance and license

Chen, D. (2012). *Online Retail II* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D.

Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii
Download: https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip
Retrieved October 14, 2026. UCI lists this dataset under **CC BY 4.0**: https://creativecommons.org/licenses/by/4.0/ . You may share/adapt it with attribution, a license link, and an indication of changes. No endorsement by the creator is implied.

`data/raw/online_retail_II.xlsx` is the original workbook. `source_manifest.txt` records its SHA-256 and per-sheet counts. Generated yearly CSVs normalize column names and format timestamps; pipeline outputs additionally trim strings, deduplicate normalized rows, filter documented exclusions and aggregate data. The delivered input contains both complete yearly sheets.

Transactions cover December 1, 2009 through December 9, 2011. Amounts are GBP. The terminal December is incomplete. Customer IDs are provided by UCI; this project adds no identity enrichment.

This dataset license is separate from the project-code license. The referenced GitHub repository had no LICENSE file at the inspected commit. No source files, SQL, images or generated outputs from that repository are redistributed here. Workflow concepts were used to guide an original implementation.
