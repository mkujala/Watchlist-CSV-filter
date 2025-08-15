# =============================================
# Watchlist Filter Script (v1.3)
# ---------------------------------------------
# Features:
# - Finds the newest .csv/.txt file in a given folder.
# - Removes symbols from the newest file that also appear in any older file.
# - Saves filtered result as <original>_filtered.csv in the same folder.
# - Automatically deletes the newest source file after filtering
#   (optional: keep it using --keep-latest).
# - Supports pattern matching (--pattern) and date filtering (--days).
# - Prints a one-line import string for TradingView.
# - Safe writing using a temporary file before replacing the final output.
# =============================================

from pathlib import Path
import sys
import re
import argparse
import tempfile
import os
from datetime import datetime

BANNER = "Watchlist Filter • v1.3"

# ------------------------------------------------
# Utility functions
# ------------------------------------------------

def strip_block_comments(text: str) -> str:
    """
    Remove block comments of the form /* ... */ from text.
    Useful if watchlist files contain embedded comment blocks.
    """
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)

def split_symbols(text: str):
    """
    Split a raw text string into a cleaned list of symbols.
    - Accepts comma-separated and/or newline-separated formats.
    - Removes whitespace, empty entries, and comment lines:
      - Starts with ###, //, or #
    """
    text = strip_block_comments(text)
    parts = re.split(r"[,\n\r]+", text)  # split on commas or line breaks
    clean = []
    for p in parts:
        s = p.strip()
        if not s:
            continue  # skip empty strings
        if s.startswith("###") or s.startswith("//") or s.startswith("#"):
            continue  # skip comments
        clean.append(s)
    return clean

def read_symbols_from_file(path: Path):
    """
    Read a file and return a list of cleaned symbols.
    Handles UTF-8 reading, ignores errors, and warns if reading fails.
    """
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[WARN] Failed to read {path.name}: {e}", file=sys.stderr)
        return []
    return split_symbols(txt)

def is_watchlist_file(p: Path):
    """
    Check if a path is a .csv or .txt file (case-insensitive).
    """
    return p.is_file() and p.suffix.lower() in (".csv", ".txt")

def list_watchlist_files(folder: Path, pattern: str | None, days: int | None):
    """
    Return a list of watchlist files in a folder.
    - If pattern is given, uses glob to filter file names (e.g., ADR_*.csv).
    - If days is given, only returns files modified in the last N days.
    - Sorted by modification time (newest first).
    """
    files = []
    candidates = folder.glob(pattern) if pattern else folder.iterdir()
    now = datetime.now()
    for p in candidates:
        if not is_watchlist_file(p):
            continue
        if days is not None:
            age_days = (now - datetime.fromtimestamp(p.stat().st_mtime)).days
            if age_days > days:
                continue
        files.append(p)
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files

def build_seen_symbols(files: list[Path]) -> set[str]:
    """
    Aggregate all symbols from the given list of files into a set.
    Using a set for O(1) lookup when filtering.
    """
    seen: set[str] = set()
    for f in files:
        syms = read_symbols_from_file(f)
        if syms:
            seen |= set(syms)
    return seen

def filter_symbols(latest_syms: list[str], seen: set[str]) -> list[str]:
    """
    Return a new list of symbols from latest_syms
    excluding those found in the 'seen' set.
    Preserves the original order.
    """
    return [s for s in latest_syms if s not in seen]

def safe_write_one_line(path: Path, symbols: list[str]) -> Path:
    """
    Safely write the filtered symbols to <stem>_filtered.txt in one line.
    Uses a temporary file and replaces the final output atomically.
    """
    out_path = path.with_name(path.stem + "_filtered.txt")
    one_line = ",".join(symbols)
    # Create temporary file in same directory
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=str(path.parent)) as tf:
        tf.write(one_line)
        tmp_name = tf.name
    os.replace(tmp_name, out_path)  # atomic replace on most OS/filesystems
    return out_path

# ------------------------------------------------
# Main logic
# ------------------------------------------------

def main():
    # ---- Parse CLI arguments ----
    ap = argparse.ArgumentParser(description="Filter newest watchlist by removing symbols found in older files.")
    ap.add_argument("folder", nargs="?", default=".", help="Folder containing .csv/.txt watchlists (default: current).")
    ap.add_argument("--pattern", help="Glob pattern to pre-filter files (e.g. 'ADR_*.csv').")
    ap.add_argument("--days", type=int, help="Only consider files modified within last N days.")
    ap.add_argument("--no-print", action="store_true", help="Do not print the one-line import string.")
    ap.add_argument("--keep-latest", action="store_true", help="Do not delete the newest file after filtering.")
    args = ap.parse_args()

    # ---- Resolve folder path ----
    base = Path(args.folder).expanduser().resolve()
    print(f"{BANNER}\nFolder: {base}")
    if not base.exists():
        print("Error: folder does not exist.", file=sys.stderr)
        sys.exit(1)

    # ---- List files in target folder ----
    files = list_watchlist_files(base, args.pattern, args.days)
    if not files:
        print("No matching .csv/.txt files found.", file=sys.stderr)
        sys.exit(0)

    # First file is the newest
    latest = files[0]
    others = files[1:]

    ts = datetime.fromtimestamp(latest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Newest file: {latest.name} (modified {ts})")

    # ---- Read newest file symbols ----
    latest_syms = read_symbols_from_file(latest)
    if not latest_syms:
        print("[WARN] Latest file contained no symbols after parsing.", file=sys.stderr)

    # ---- If there are no older files, just normalize output ----
    if not others:
        print("No older files to compare; will normalize and output anyway.")
        out = safe_write_one_line(latest, latest_syms)
        if not args.no_print:
            print("\n=== ONE-LINE IMPORT STRING ===")
            print(",".join(latest_syms))
        print(f"Written: {out}")
        # Remove the newest source file unless keep-latest is specified
        if not args.keep_latest:
            try:
                latest.unlink()
                print(f"Deleted source: {latest.name}")
            except Exception as e:
                print(f"[WARN] Failed to delete {latest.name}: {e}", file=sys.stderr)
        return

    # ---- Build set of seen symbols from older files ----
    seen = build_seen_symbols(others)

    # ---- Filter newest symbols ----
    filtered = filter_symbols(latest_syms, seen)

    # ---- Report stats ----
    removed = len(latest_syms) - len(filtered)
    print(f"Original: {len(latest_syms)} • Removed (found in older files): {removed} • Remaining: {len(filtered)}")

    # ---- Write filtered result ----
    out = safe_write_one_line(latest, filtered)
    print(f"Written: {out}")

    # ---- Print one-line output unless disabled ----
    if not args.no_print:
        print("\n=== ONE-LINE IMPORT STRING ===")
        print(",".join(filtered))

    # ---- Delete newest source file unless keep-latest is specified ----
    if not args.keep_latest:
        try:
            latest.unlink()
            print(f"Deleted source: {latest.name}")
        except Exception as e:
            print(f"[WARN] Failed to delete {latest.name}: {e}", file=sys.stderr)

# ------------------------------------------------
# Entry point
# ------------------------------------------------
if __name__ == "__main__":
    main()

# ------------------------------------------------
# End of script
