# TradingView Watchlist Filter

A lightweight Python script to filter your newest TradingView watchlist by removing any symbols that appear in older watchlist files from the same folder.

## Features
- Finds the newest `.csv`/`.txt` file in a given folder.
- Removes all symbols found in any other (older) watchlist file in that folder.
- Preserves the original order of symbols.
- Accepts comma-separated and/or newline-separated formats.
- Skips comment lines starting with `#`, `###`, or `//`.
- Prints a **one-line, comma-separated import string** for TradingView.
- Saves the filtered watchlist as `<original>_filtered.csv`.

## Requirements
- Python **3.8+** (recommended: Python 3.12)
- No third-party dependencies required.

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
ADR 6.8.25.csv
ADR 7.8.25.csv  <- newest file
```

Running:
```bash
python filter_latest_watchlist.py .
```

Will:
- Detect `ADR 7.8.25.csv` as the newest.
- Remove any symbols found in `ADR 5.8.25.csv` or `ADR 6.8.25.csv`.
- Save results to `ADR 7.8.25_filtered.csv`.
- Print the one-line TradingView import string to the terminal.

### Options (v1.2+)
```bash
--pattern "ADR*.csv"   # Only consider files matching glob pattern
--days 7               # Only consider files modified in last 7 days
--no-print             # Do not print the import string to stdout
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

## Example Output
```plaintext
Watchlist Filter • v1.1
Folder: C:\dev\watchlists
Newest file: ADR 7.8.25.csv (modified 2025-08-15 10:35:00)
Original: 50 • Removed (found in older files): 8 • Remaining: 42
Written: ADR 7.8.25_filtered.csv

=== ONE-LINE IMPORT STRING ===
NASDAQ:AAOI,NASDAQ:ALAB,NASDAQ:GOOGL,NASDAQ:META
```

## License
MIT License – free to use, modify, and distribute.
