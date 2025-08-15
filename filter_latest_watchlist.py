# =============================================
# Watchlist Filter Script (v1.4)
# ---------------------------------------------
# Modes:
# 1) Default (FILTER): Filter newest file against older ones -> <stem>_filtered.txt
#    - Deletes newest source after success (disable with --keep-latest)
# 2) --combine: Combine ALL files into a unique union -> <newest_stem>_combined.txt
#    - Does NOT delete any source files
# Common:
#  - Accepts .csv and .txt inputs
#  - One-line output (comma-separated)
#  - Skips lines starting with ###, //, #
#  - Safe write via temp file then atomic replace
# =============================================

from pathlib import Path
import sys
import re
import argparse
import tempfile
import os
from datetime import datetime

BANNER = "Watchlist Filter • v1.4"

# -------------- Parsing utilities --------------

def strip_block_comments(text: str) -> str:
    """Remove /* ... */ blocks."""
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)

def split_symbols(text: str):
    """
    Split raw text into cleaned symbols.
    - Accept commas and newlines as separators.
    - Trim whitespace.
    - Drop empty entries and comment lines (###, //, #).
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
    """Read file and return parsed symbol list. Warn if reading fails."""
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[WARN] Failed to read {path.name}: {e}", file=sys.stderr)
        return []
    return split_symbols(txt)

def is_watchlist_file(p: Path):
    """Accept .csv or .txt files."""
    return p.is_file() and p.suffix.lower() in (".csv", ".txt")

def list_watchlist_files(folder: Path, pattern: str | None, days: int | None):
    """
    Return files sorted by mtime (newest first).
    - pattern: optional glob (e.g., 'ADR_*.*')
    - days: only files modified within last N days
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

# -------------- Core ops --------------

def build_seen_symbols(files: list[Path]) -> set[str]:
    """Aggregate symbols from older files into a set for O(1) lookup."""
    seen: set[str] = set()
    for f in files:
        syms = read_symbols_from_file(f)
        if syms:
            seen |= set(syms)
    return seen

def filter_symbols(latest_syms: list[str], seen: set[str]) -> list[str]:
    """Filter out any symbol present in 'seen', preserving order."""
    return [s for s in latest_syms if s not in seen]

def combine_files_unique(files: list[Path]) -> list[str]:
    """
    Create a unique union of symbols across ALL files.
    Order rule: first-seen wins by scanning files from OLDEST -> NEWEST,
    preserving symbol order inside each file.
    """
    ordered_unique: list[str] = []
    seen: set[str] = set()
    # files are passed as NEWEST->OLDEST; we want OLDEST first:
    for f in reversed(files):
        for s in read_symbols_from_file(f):
            if s not in seen:
                seen.add(s)
                ordered_unique.append(s)
    return ordered_unique

# -------------- Safe write helpers (always .txt) --------------

def write_one_line_txt(out_path: Path, symbols: list[str]) -> Path:
    """Write one-line, comma-separated .txt safely (temp -> replace)."""
    one_line = ",".join(symbols)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=str(out_path.parent)) as tf:
        tf.write(one_line)
        tmp_name = tf.name
    os.replace(tmp_name, out_path)
    return out_path

def safe_write_filtered_txt(base: Path, symbols: list[str]) -> Path:
    """Write <stem>_filtered.txt next to base file."""
    out_path = base.with_name(base.stem + "_filtered.txt")
    return write_one_line_txt(out_path, symbols)

def safe_write_combined_txt(base: Path, symbols: list[str]) -> Path:
    """Write <newest_stem>_combined.txt next to newest file."""
    out_path = base.with_name(base.stem + "_combined.txt")
    return write_one_line_txt(out_path, symbols)

# -------------- CLI --------------

def main():
    ap = argparse.ArgumentParser(description="Filter newest watchlist or combine all into a unique list.")
    ap.add_argument("folder", nargs="?", default=".", help="Folder containing .csv/.txt watchlists (default: current).")
    ap.add_argument("--pattern", help="Glob pattern to pre-filter files (e.g. 'ADR_*.*').")
    ap.add_argument("--days", type=int, help="Only consider files modified within last N days.")
    ap.add_argument("--no-print", action="store_true", help="Do not print the one-line import string.")
    ap.add_argument("--keep-latest", action="store_true", help="Do not delete the newest file after filtering.")
    ap.add_argument("--combine", action="store_true", help="Combine ALL files into a unique union -> <newest_stem>_combined.txt (no deletion).")
    args = ap.parse_args()

    base = Path(args.folder).expanduser().resolve()
    print(f"{BANNER}\nFolder: {base}")
    if not base.exists():
        print("Error: folder does not exist.", file=sys.stderr)
        sys.exit(1)

    files = list_watchlist_files(base, args.pattern, args.days)
    if not files:
        print("No matching .csv/.txt files found.", file=sys.stderr)
        sys.exit(0)

    newest = files[0]
    others = files[1:]
    ts = datetime.fromtimestamp(newest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Newest file: {newest.name} (modified {ts})")

    # ---- COMBINE MODE ----
    if args.combine:
        combined = combine_files_unique(files)
        print(f"Combine mode: files={len(files)} • unique symbols={len(combined)}")
        out = safe_write_combined_txt(newest, combined)
        print(f"Written: {out}")
        if not args.no_print:
            print("\n=== ONE-LINE IMPORT STRING (COMBINED) ===")
            print(",".join(combined))
        # Never delete sources in combine mode
        return

    # ---- FILTER MODE (default) ----
    newest_syms = read_symbols_from_file(newest)
    if not newest_syms:
        print("[WARN] Newest file contained no symbols after parsing.", file=sys.stderr)

    if not others:
        print("No older files to compare; will normalize and output anyway.")
        out = safe_write_filtered_txt(newest, newest_syms)
        if not args.no_print:
            print("\n=== ONE-LINE IMPORT STRING ===")
            print(",".join(newest_syms))
        print(f"Written: {out}")
        if not args.keep_latest:
            try:
                newest.unlink()
                print(f"Deleted source: {newest.name}")
            except Exception as e:
                print(f"[WARN] Failed to delete {newest.name}: {e}", file=sys.stderr)
        return

    seen = build_seen_symbols(others)
    filtered = filter_symbols(newest_syms, seen)

    removed = len(newest_syms) - len(filtered)
    print(f"Original: {len(newest_syms)} • Removed (in older files): {removed} • Remaining: {len(filtered)}")

    out = safe_write_filtered_txt(newest, filtered)
    print(f"Written: {out}")

    if not args.no_print:
        print("\n=== ONE-LINE IMPORT STRING ===")
        print(",".join(filtered))
        print()

    if not args.keep_latest:
        try:
            newest.unlink()
            print(f"Deleted source: {newest.name}")
        except Exception as e:
            print(f"[WARN] Failed to delete {newest.name}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
