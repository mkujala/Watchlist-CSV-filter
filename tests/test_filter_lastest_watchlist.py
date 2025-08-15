# tests/test_filter_latest_watchlist.py
import os
import sys
import subprocess
from pathlib import Path
import time

def write(p: Path, content: str):
    p.write_text(content, encoding="utf-8")

def test_filters_newest_against_older_files(tmp_path: Path):
    """
    Setup:
      - older1.txt  (symbols: NASDAQ:AAPL,NASDAQ:MSFT,NASDAQ:NVDA)
      - older2.csv  (symbols: NASDAQ:TSLA,NASDAQ:AMZN)
      - newest.csv  (symbols: NASDAQ:AAPL,NASDAQ:GOOGL,NASDAQ:AMZN,NASDAQ:META)

    Expect:
      - newest_filtered.csv contains only symbols not in older files,
        preserving order: NASDAQ:GOOGL,NASDAQ:META
      - stdout contains ONE-LINE IMPORT STRING with same content.
    """
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "filter_latest_watchlist.py"
    assert script.exists(), f"Script not found at: {script}"

    # Create three files in tmp dir
    older1 = tmp_path / "older1.txt"
    older2 = tmp_path / "older2.csv"
    newest = tmp_path / "newest.csv"

    write(older1, "NASDAQ:AAPL,NASDAQ:MSFT,NASDAQ:NVDA")
    write(older2, "NASDAQ:TSLA\nNASDAQ:AMZN")
    write(newest, "NASDAQ:AAPL,NASDAQ:GOOGL,NASDAQ:AMZN,NASDAQ:META")

    # Set mtimes so 'newest.csv' is the newest
    now = time.time()
    os.utime(older1, (now - 300, now - 300))  # 5 min ago
    os.utime(older2, (now - 200, now - 200))  # ~3 min ago
    os.utime(newest, (now - 100, now - 100))  # ~1.5 min ago (newest)

    # Run the script against tmp_path
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        capture_output=True,
        text=True,
        check=True
    )

    # Check output file
    out_file = tmp_path / "newest_filtered.csv"
    assert out_file.exists(), "Filtered output file not created."
    content = out_file.read_text(encoding="utf-8")
    assert content == "NASDAQ:GOOGL,NASDAQ:META", f"Unexpected filtered content: {content}"

    # Check stdout one-line print
    stdout = result.stdout
    assert "ONE-LINE IMPORT STRING" in stdout
    assert "NASDAQ:GOOGL,NASDAQ:META" in stdout
