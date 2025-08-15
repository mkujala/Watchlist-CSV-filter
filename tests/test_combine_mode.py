# tests/test_combine_mode.py
import os
import sys
import subprocess
from pathlib import Path
import time

def write(p: Path, content: str):
    """Helper to write text content."""
    p.write_text(content, encoding="utf-8")

def test_combine_mode_creates_union_once_preserving_first_seen_order(tmp_path: Path):
    """
    Setup (note mixed .csv/.txt extensions):
      - older1.csv : AAPL,MSFT,GOOG
      - mid.txt    : MSFT,TSLA,NVDA
      - newest.csv : GOOG,META,NVDA,AMZN

    Expected combined (first-seen order scanning oldest -> newest):
      AAPL,MSFT,GOOG,TSLA,NVDA,META,AMZN

    Also expect:
      - Output file name: newest_stem + '_combined.txt' (here: 'newest_combined.txt')
      - Source files are NOT deleted in --combine mode
      - Stdout contains ONE-LINE IMPORT STRING (COMBINED) with same content
    """
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "filter_latest_watchlist.py"
    assert script.exists(), f"Script not found at: {script}"

    # Create files
    older1 = tmp_path / "older1.csv"
    mid    = tmp_path / "mid.txt"
    newest = tmp_path / "newest.csv"

    write(older1, "NASDAQ:AAPL,NASDAQ:MSFT,NASDAQ:GOOG")
    write(mid,    "NASDAQ:MSFT\nNASDAQ:TSLA\nNASDAQ:NVDA")
    write(newest, "NASDAQ:GOOG,NASDAQ:META,NASDAQ:NVDA,NASDAQ:AMZN")

    # Set mtimes so newest is really the newest
    now = time.time()
    os.utime(older1, (now - 300, now - 300))  # oldest
    os.utime(mid,    (now - 200, now - 200))  # middle
    os.utime(newest, (now - 100, now - 100))  # newest

    # Run in combine mode
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path), "--combine"],
        capture_output=True,
        text=True,
        check=True
    )

    # Expected
    expected = "NASDAQ:AAPL,NASDAQ:MSFT,NASDAQ:GOOG,NASDAQ:TSLA,NASDAQ:NVDA,NASDAQ:META,NASDAQ:AMZN"

    # Check output file
    out_file = tmp_path / "newest_combined.txt"
    assert out_file.exists(), "Combined output file not created."
    content = out_file.read_text(encoding="utf-8")
    assert content == expected, f"Unexpected combined content:\n{content}"

    # Stdout should include the combined one-liner
    stdout = result.stdout
    assert "ONE-LINE IMPORT STRING (COMBINED)" in stdout
    assert expected in stdout

    # Source files must NOT be deleted in --combine mode
    assert older1.exists(), "older1.csv should not be deleted in --combine mode"
    assert mid.exists(),    "mid.txt should not be deleted in --combine mode"
    assert newest.exists(), "newest.csv should not be deleted in --combine mode"
