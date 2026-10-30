"""Part 2 — the readings API: upload a CSV of substation readings through the API, then ask questions about them.
Run:   python 3_readings_api.py       or   uvicorn 3_readings_api:app --reload --port 8001
       Port 8001, so it runs next to the calculator API (8000). Another port: python 3_readings_api.py 8011
Open:  http://127.0.0.1:8001/docs        ← POST /readings/upload has a "Choose file" button: pick campus_feb_mar_2026.csv
Or:    python 4_upload_csv.py            ← a program that uploads the file to the running API"""
from datetime import date, datetime

from fastapi import FastAPI, File, HTTPException, Query, UploadFile

import readings

app = FastAPI(title="Readings API", version="v2-part-2",
              description="Upload the campus substation's readings as a CSV, then ask: what's loaded, one day, the worst days.")


def answer(fn, *args):
    """Call the logic; turn its refusals into HTTP status codes. 404 = no such data, 400 = the request can't be done."""
    try:
        return fn(*args)
    except readings.NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/")
def home():
    return {"message": "Readings API is running. Open /docs, then POST /readings/upload with the CSV."}


# ── Load and remove ─────────────────────────────────────────────────────────────────────────────────
@app.post("/readings/upload", status_code=201)
async def upload(file: UploadFile = File(description="a CSV with timestamp, load_kw, solar_kw, ambient_c, irradiance_wm2"),
                 replace: bool = Query(True, description="true: replace everything; false: add only times not loaded yet")):
    """Upload a CSV file of readings. Every row is checked; the report says what was loaded and what was refused, and why."""
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail=f"'{file.filename}' is not a .csv file")
    return answer(readings.load_csv, await file.read(), replace)


@app.delete("/readings")
def delete_readings():
    """Remove every reading — to start again."""
    return {"deleted": readings.delete_all()}


# ── Ask ─────────────────────────────────────────────────────────────────────────────────────────────
@app.get("/readings/stats")
def stats():
    """How many readings are loaded, and from when to when."""
    return readings.stats()


@app.get("/readings")
def get_readings(start: datetime = Query(examples=["2026-03-23T12:00"]), end: datetime = Query(examples=["2026-03-23T13:00"])):
    """The raw 15-minute readings from start to end (end not included) — at most 7 days at a time."""
    return answer(readings.get_readings, start, end)


@app.get("/summary")
def summary(day: date = Query(examples=["2026-03-23"])):
    """One day in numbers: peak load, energy, solar, the transformer's peak loading and status (NORMAL / HIGH / OVERLOAD)."""
    return answer(readings.summary, day)


@app.get("/peak-days")
def peak_days(top: int = Query(5, ge=1, le=31, description="how many days")):
    """The days when the transformer worked hardest, highest loading first."""
    return readings.peak_days(top)



if __name__ == "__main__":                       # python 3_readings_api.py works too — from any folder; another port: python 3_readings_api.py 8011
    import sys
    from pathlib import Path

    import uvicorn
    here = Path(__file__).resolve().parent
    uvicorn.run("3_readings_api:app", app_dir=str(here), reload=True, reload_dirs=[str(here)],
                host="127.0.0.1", port=int(sys.argv[1]) if len(sys.argv) > 1 else 8001)
