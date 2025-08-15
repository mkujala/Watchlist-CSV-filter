# TradingView Watchlist Filter

A lightweight Python script to filter your newest TradingView watchlist by removing any symbols that appear in older watchlist files from the same folder — or to **combine** all lists into one de‑duplicated file.

## Features
- Finds the newest `.csv`/`.txt` file in a given folder.
- **Filter mode (default):** removes all symbols from the newest file that are present in any older file; saves `<stem>_filtered.txt` **next to the newest file** and deletes the newest source file (can be disabled with `--keep-latest`).
- **Combine mode (`--combine`):** creates a **union** of symbols across **all** files (each symbol appears once), preserves first-seen order (oldest → newest), saves `<newest_stem>_combined.txt`, and **does not delete** any source files.
- Accepts comma-separated and/or newline-separated formats; supports both `.csv` and `.txt` inputs.
- Skips comment lines starting with `#`, `###`, or `//`.
- Prints a one-line, comma-separated import string for TradingView.
- Safe file writing using a temporary file before replacing the output.

## Requirements
- Python 3.8+ (recommended: Python 3.12)
- No third-party dependencies required.

## Recommended Folder Structure

Organize watchlist files by month in the `data/` folder. This keeps files tidy and makes it easy to start clean each month.

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
- Files can be **either `.csv` or `.txt`** — the script supports both formats.
- Place each daily watchlist file into the appropriate month folder.

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

### Filter mode (default)
Run the script in the folder containing your watchlist files:

```bash
python filter_latest_watchlist.py /path/to/folder
```
or with a glob pattern (recommended):
```bash
python filter_latest_watchlist.py data/2025-08 --pattern "ADR_*.*"
```

What happens:
- Detects the newest file by modified time.
- Removes any symbols found in older files.
- Saves `<stem>_filtered.txt` next to the newest file.
- Prints the one-line TradingView import string.
- Deletes the newest source file (unless `--keep-latest` is used).

### Combine mode
Create a single de‑duplicated list from **all** files in the folder:

```bash
python filter_latest_watchlist.py data/2025-08 --pattern "ADR_*.*" --combine
```
What happens:
- Scans files from **oldest to newest** to preserve first-seen order.
- Each symbol appears **once** in the result.
- Saves `<newest_stem>_combined.txt` next to the newest file.
- **Does not delete** any source files.

### Options (v1.4+)
```bash
--pattern "ADR_*.*"   # Only consider files matching glob pattern
--days 7              # Only consider files modified in last 7 days
--no-print            # Do not print the import string to stdout
--keep-latest         # Do not delete the newest file after filtering (filter mode only)
--combine             # Combine ALL files into a unique union (no deletions)
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

The test suite verifies that:
- The script detects the newest file correctly.
- Filter mode removes symbols found in older files and deletes the newest file.
- Combine mode produces a once-only union in first-seen order and does not delete sources.

## Example Output

**Filter mode:**
```plaintext
Watchlist Filter • v1.4
Folder: C:\dev\watchlists\data\2025-08
Newest file: ADR_2025-08-15.csv (modified 2025-08-15 10:35:00)
Original: 50 • Removed (in older files): 8 • Remaining: 42
Written: ADR_2025-08-15_filtered.txt
Deleted source: ADR_2025-08-15.csv

=== ONE-LINE IMPORT STRING ===
NASDAQ:AAOI,NASDAQ:ALAB,NASDAQ:GOOGL,NASDAQ:META
```

**Combine mode:**
```plaintext
Watchlist Filter • v1.4
Folder: C:\dev\watchlists\data\2025-08
Combine mode: files=15 • unique symbols=127
Written: ADR_2025-08-15_combined.txt

=== ONE-LINE IMPORT STRING (COMBINED) ===
NASDAQ:AAPL,NASDAQ:MSFT,NASDAQ:GOOGL,...
```

## License
MIT License – free to use, modify, and distribute.
