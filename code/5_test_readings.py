"""Part 2 — every endpoint of the RUNNING readings API, called over HTTP, with the reply printed.
Start the API first:   python 3_readings_api.py          (port 8001)
Then, in a second terminal:   python 5_test_readings.py
It empties the database first and ends with the 5,664 readings loaded again, so /docs then has data to show.
API on another port?   API_URL=http://127.0.0.1:8011 python 5_test_readings.py"""
import json
import os
import sys
from pathlib import Path

import httpx

API = os.environ.get("API_URL", "http://127.0.0.1:8001")         # where 3_readings_api.py runs
DATA = Path(__file__).resolve().parent                            # the CSV files are in this folder
client = httpx.Client(base_url=API, timeout=60)

try:                                                              # first ask WHO is on that port: it must be the Readings API
    who = client.get("/").json().get("message", "")
except httpx.ConnectError:
    sys.exit(f"✗ Nothing is running at {API}. Start the API first:  python 3_readings_api.py")
if "Readings API" not in who:
    sys.exit(f"✗ The program at {API} is not the Readings API ({who}). Start it:  python 3_readings_api.py")
print(f"Testing the Readings API at {API}\n")


def show(method, url, reply_max=230, **kw):
    r = client.request(method, url, **kw)
    reply = r.json()
    if r.status_code == 422:                                   # FastAPI explains every broken rule; show the first one
        e = reply["detail"][0]
        reply = f"{e['msg']}  (in {e['loc'][0]}: {e['loc'][-1]})"
    print(f"{method:<6} {url:<52} → {r.status_code}  {reply if isinstance(reply, str) else json.dumps(reply, ensure_ascii=False)[:reply_max]}")
    return r.json()


def upload(name, url="/readings/upload"):
    """Send a file the way a browser does; print the upload report's totals instead of its raw JSON."""
    with open(DATA / name, "rb") as f:
        r = client.post(url, files={"file": (name, f, "text/csv")})
    rep, db = r.json(), r.json()["database"]
    print(f"POST   {url + '  (' + name + ')':<52} → {r.status_code}  loaded {rep['loaded']:,} of {rep['rows_in_file']:,} · "
          f"already there {rep['already_in_database']:,} · refused {rep['rejected']} → database: {db['readings']:,} readings")
    return rep


print("1 · Start empty")
show("DELETE", "/readings")
show("GET", "/readings/stats")
show("GET", "/summary?day=2026-03-23")                         # 404: nothing loaded yet

print("\n2 · Upload a file with mistakes — every row is checked")
report = upload("readings_with_problems.csv")
for p in report["problems"]:
    print(f"         line {p['line']}: {p['problem']}")

print("\n3 · Upload the real file: 5,664 readings")
for url in ["/readings/upload", "/readings/upload?replace=false"]:     # replace, then add mode: nothing new to add
    upload("campus_feb_mar_2026.csv", url)

print("\n4 · Ask questions")
show("GET", "/readings/stats")
show("GET", "/summary?day=2026-03-23")
show("GET", "/peak-days?top=3", 400)
show("GET", "/readings?start=2026-03-23T12:00&end=2026-03-23T13:00", 180)

print("\n5 · Refused, with a reason")
show("GET", "/summary?day=2026-05-01")                         # 404: no data for that day
show("GET", "/readings?start=2026-02-01T00:00&end=2026-03-01T00:00")   # 400: more than 7 days
show("GET", "/peak-days?top=0")                                # 422: top must be 1–31
show("POST", "/readings/upload", files={"file": ("notes.txt", b"hello", "text/plain")})   # 400: not a .csv
show("POST", "/readings/upload", files={"file": ("wrong.csv", b"time,kw\n2026-03-01 00:00,100", "text/csv")})  # 400: wrong columns
