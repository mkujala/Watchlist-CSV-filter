# TradingView Watchlist Filter

A lightweight Python script to filter your newest TradingView watchlist by removing any symbols that appear in older watchlist files from the same folder.

## Features
- Finds the newest `.csv`/`.txt` file in a given folder.
- Removes all symbols found in any other (older) watchlist file in that folder.
- Saves the filtered watchlist as `<original>_filtered.csv` in the **same folder** as the newest file.
- Automatically **deletes the newest source file** after creating the `_filtered.txt` version (disable with `--keep-latest`).
- Preserves the original order of symbols.
- Accepts comma-separated and/or newline-separated formats.
- Skips comment lines starting with `#`, `###`, or `//`.
- Prints a one-line, comma-separated import string for TradingView.
- Safe file writing using a temporary file before replacing the output.

## Requirements
- Python 3.8+ (recommended: Python 3.12)
- No third-party dependencies required.

## Recommended Folder Structure

It is recommended to organize watchlist files by month in the `data/` folder.  
This keeps files tidy and makes it easy to start with a clean folder each month.

Example structure:
```
project-root/
├─ data/
│  ├─ 2025-07/
│  │  ├─ ADR_2025-07-05.csv
│  │  ├─ ADR_2025-07-06.csv
│  │  └─ ...
│  ├─ 2025-08/
│  │  ├─ ADR_2025-08-05.txt
│  │  ├─ ADR_2025-08-06.txt
│  │  └─ ...
├─ filter_latest_watchlist.py
├─ README.md
└─ .gitignore
```

- **`data/YYYY-MM`** → Holds all watchlists for that month.
- Files can be **either `.csv` or `.txt`** — the script supports both formats.
- Place each daily watchlist file into the appropriate month folder.
- Run the script in that month's folder to process the latest file.

Example run for August:
```bash
python filter_latest_watchlist.py data/2025-08 --pattern "ADR_*.*"
```

Filtered output will be written to the same month folder.  
By default, the newest source file is deleted after processing unless `--keep-latest` is provided.

## Installation
Clone this repository and navigate into it:

```bash
git clone https://github.com/<your-username>/watchlist-filter.git
cd watchlist-filter
```

(Optional) Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows
```

## Usage

### Basic
Run the script in the folder containing your watchlist files:

```bash
python filter_latest_watchlist.py /path/to/folder
```

If no folder is given, the current directory is used.

### Example
Folder contains:
```
ADR 5.8.25.csv
ADR 6.8.25.txt
ADR 7.8.25.csv  <- newest file
```

Running:
```bash
python filter_latest_watchlist.py .
```

Will:
- Detect `ADR 7.8.25.csv` as the newest.
- Remove any symbols found in `ADR 5.8.25.csv` or `ADR 6.8.25.txt`.
- Save results to `ADR 7.8.25_filtered.txt` in the same folder.
- Print the one-line TradingView import string to the terminal.
- Delete `ADR 7.8.25.csv` after creating the filtered version (unless `--keep-latest` is used).

### Options (v1.3+)
```bash
--pattern "ADR*.csv"   # Only consider files matching glob pattern
--days 7               # Only consider files modified in last 7 days
--no-print             # Do not print the import string to stdout
--keep-latest          # Do not delete the newest file after filtering
```

## Development & Testing

### Install dev dependencies
```bash
pip install pytest
```

### Run tests
```bash
pytest -q
```

Tests create temporary files and verify that:
- The script detects the newest file correctly.
- Symbols present in older files are removed from the newest file.
- Output matches expected format.
- The newest file is deleted after processing unless `--keep-latest` is specified.

## Example Output
```plaintext
Watchlist Filter • v1.3
Folder: C:\dev\watchlists\data\2025-08
Newest file: ADR_2025-08-15.csv (modified 2025-08-15 10:35:00)
Original: 50 • Removed (found in older files): 8 • Remaining: 42
Written: ADR_2025-08-15_filtered.txt
Deleted source: ADR_2025-08-15.csv

=== ONE-LINE IMPORT STRING ===
NASDAQ:AAOI,NASDAQ:ALAB,NASDAQ:GOOGL,NASDAQ:META
```

## License
MIT License – free to use, modify, and distribute.
