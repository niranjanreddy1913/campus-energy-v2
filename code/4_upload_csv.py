"""Part 2 — a program that loads data THROUGH the API: it sends the CSV file to POST /readings/upload, like the
"Choose file" button in /docs does. Start the API first (python 3_readings_api.py — port 8001), then, in a second terminal:
    python 4_upload_csv.py                               ← the 5,664 readings
    python 4_upload_csv.py readings_with_problems.csv    ← a file with mistakes: see what the API refuses
API on another port?  API_URL=http://127.0.0.1:8011 python 4_upload_csv.py"""
import json
import os
import sys
from pathlib import Path

import httpx

API = os.environ.get("API_URL", "http://127.0.0.1:8001")         # where 3_readings_api.py runs
HERE = Path(__file__).resolve().parent                # the CSV files are in this folder
FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "campus_feb_mar_2026.csv"
if not FILE.exists() and (HERE / FILE).exists():       # a bare file name: look next to this program too
    FILE = HERE / FILE

try:                                                    # first ask WHO is on that port: it must be the Readings API
    who = httpx.get(f"{API}/", timeout=5).json().get("message", "")
except httpx.ConnectError:
    sys.exit(f"✗ Nothing is running at {API}. Start the API first:  python 3_readings_api.py")
except ValueError:
    who = ""
if "Readings API" not in who:
    sys.exit(f"✗ The program at {API} is not the Readings API ({who or 'it did not say what it is'}).\n"
             f"  Start the Readings API:  python 3_readings_api.py   (it uses port 8001)")

print(f"Uploading {FILE.name} ({FILE.stat().st_size // 1024} KB) to {API}/readings/upload …")
with open(FILE, "rb") as f:                             # multipart/form-data: the same way a browser sends a file
    r = httpx.post(f"{API}/readings/upload", files={"file": (FILE.name, f, "text/csv")}, timeout=60)
print(f"→ {r.status_code}")
print(json.dumps(r.json(), indent=2))
