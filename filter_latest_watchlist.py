# =============================================
# Watchlist Filter Script (v1.2)
# - Robust error handling
# - Set-union for faster symbol aggregation
# - Modularized functions
# - Supports block comments /* ... */ and line comments (//, #, ###)
# - File pre-filtering with --pattern and time window with --days
# - Prints one-line import string and writes <latest>_filtered.csv
# =============================================

from pathlib import Path
import sys
import re
import argparse
from datetime import datetime, timedelta

BANNER = "Watchlist Filter • v1.2"

# ---------- Parsing & utility ----------

def strip_block_comments(text: str) -> str:
    """Remove C-style block comments /* ... */."""
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)

def split_symbols(text: str):
    """
    Split by comma or newline; trim whitespace; drop comments/empty.
    Supports:
      - block comments:  /* ... */
      - line comments:   //..., #..., ###...
    """
    text = strip_block_comments(text)
    parts = re.split(r"[,\n\r]+", text)
    clean = []
    for p in parts:
        s = p.strip()
        if not s:
            continue
        if s.startswith("###") or s.startswith("//") or s.startswith("#"):
            continue
        clean.append(s)
    return clean

def read_symbols_from_file(path: Path):
    """Read file content and return list of cleaned symbols. Logs errors."""
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[WARN] Failed to read {path.name}: {e}", file=sys.stderr)
        return []
    return split_symbols(txt)

def is_watchlist_file(p: Path):
    """Accept only .csv/.txt regular files."""
    return p.is_file() and p.suffix.lower() in (".csv", ".txt")

def list_watchlist_files(folder: Path, pattern: str | None, days: int | None):
    """
    Collect .csv/.txt files filtered by optional glob pattern and age.
    Sorted by modified time (newest first).
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
    """Aggregate symbols from all given files using set union."""
    seen: set[str] = set()
    for f in files:
        syms = read_symbols_from_file(f)
        if syms:
            seen |= set(syms)
    return seen

def filter_symbols(latest_syms: list[str], seen: set[str]) -> list[str]:
    """Filter out any symbol present in 'seen', preserving original order."""
    return [s for s in latest_syms if s not in seen]

def write_one_line_csv(path: Path, symbols: list[str]) -> Path:
    """Write a single-line, comma-separated file; return output path."""
    out = path.with_name(path.stem + "_filtered.csv")
    out.write_text(",".join(symbols), encoding="utf-8")
    return out

# ---------- Main flow ----------

def main():
    ap = argparse.ArgumentParser(description="Filter newest watchlist by removing symbols found in older files.")
    ap.add_argument("folder", nargs="?", default=".", help="Folder containing .csv/.txt watchlists (default: current).")
    ap.add_argument("--pattern", help="Glob pattern to pre-filter files (e.g. 'ADR*.csv').")
    ap.add_argument("--days", type=int, help="Only consider files modified within last N days.")
    ap.add_argument("--no-print", action="store_true", help="Do not print the one-line import string.")
    args = ap.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    print(f"{BANNER}\nFolder: {folder}")
    if not folder.exists():
        print("Error: folder does not exist.", file=sys.stderr)
        sys.exit(1)

    files = list_watchlist_files(folder, args.pattern, args.days)
    if not files:
        print("No matching .csv/.txt files found.", file=sys.stderr)
        sys.exit(0)

    latest = files[0]
    others = files[1:]

    ts = datetime.fromtimestamp(latest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Newest file: {latest.name} (modified {ts})")

    latest_syms = read_symbols_from_file(latest)
    if not latest_syms:
        print(f"[WARN] Latest file contained no symbols after parsing.", file=sys.stderr)

    if not others:
        print("No older files to compare; will normalize and output anyway.")
        out = write_one_line_csv(latest, latest_syms)
        if not args.no_print:
            print("\n=== ONE-LINE IMPORT STRING ===")
            print(",".join(latest_syms))
        print(f"Written: {out}")
        return

    seen = build_seen_symbols(others)
    filtered = filter_symbols(latest_syms, seen)

    removed = len(latest_syms) - len(filtered)
    print(f"Original: {len(latest_syms)} • Removed (found in older files): {removed} • Remaining: {len(filtered)}")

    out = write_one_line_csv(latest, filtered)
    print(f"Written: {out}")

    if not args.no_print:
        print("\n=== ONE-LINE IMPORT STRING ===")
        print(",".join(filtered))

if __name__ == "__main__":
    main()
