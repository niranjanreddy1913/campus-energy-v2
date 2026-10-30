"""readings.py — the logic for the substation readings: check and load a CSV, then answer questions about it.
No FastAPI here. 3_readings_api.py (REST) calls these functions today; in Part 3 the MCP server calls the SAME ones."""
import io
from datetime import date, datetime, timedelta

import pandas as pd
from sqlalchemy import delete, func, select

from db import Reading, Session

COLUMNS = ["timestamp", "load_kw", "solar_kw", "ambient_c", "irradiance_wm2"]
LIMITS = {"load_kw": (0, 2000), "solar_kw": (0, 500), "ambient_c": (-10, 55), "irradiance_wm2": (0, 1500)}   # what is physically possible
RATING_KVA, PF = 630, 0.93                     # transformer TR-MAIN: its rating, and the campus power factor
MAX_DAYS = 7                                   # /readings returns at most a week (672 rows) at a time


class NotFound(Exception):
    """Asked for data that isn't there (a day with no readings). The API turns it into 404."""


# ── 1 · Load: check every row, keep the good ones, report the rest ─────────────────────────────────
def load_csv(content: bytes, replace: bool = True) -> dict:
    """Load readings from the bytes of a CSV file. replace=True empties the table first; False adds only new times."""
    try:
        df = pd.read_csv(io.BytesIO(content), dtype=str)
    except Exception:
        raise ValueError("this is not a readable CSV file")
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {', '.join(missing)}. The file has: {', '.join(df.columns)}")

    problems, good, seen = [], [], set()
    for i, row in df.iterrows():
        line = i + 2                                           # line 1 is the header
        why = _check(row)
        if not why and row["timestamp"] in seen:
            why = f"duplicate time {row['timestamp']} (already earlier in this file)"
        if why:
            problems.append({"line": line, "problem": why})
            continue
        seen.add(row["timestamp"])
        good.append(Reading(timestamp=datetime.fromisoformat(row["timestamp"]),
                            **{c: float(row[c]) for c in LIMITS}))

    with Session() as s:
        if replace:
            s.execute(delete(Reading))
            new = good
        else:                                                  # add mode: skip times the database already has
            have = set(s.scalars(select(Reading.timestamp)))
            new = [r for r in good if r.timestamp not in have]
        s.add_all(new)
        s.commit()
    return {"rows_in_file": len(df), "loaded": len(new), "already_in_database": len(good) - len(new),
            "rejected": len(problems), "problems": problems[:10], "database": stats()}


def _check(row) -> str | None:
    """Why this row can't be loaded — or None if it's fine."""
    try:
        datetime.fromisoformat(str(row["timestamp"]))
    except ValueError:
        return f"timestamp '{row['timestamp']}' is not a real date and time"
    for col, (lo, hi) in LIMITS.items():
        value = row[col]
        if pd.isna(value) or str(value).strip() == "":
            return f"{col} is empty"
        try:
            number = float(value)
        except ValueError:
            return f"{col} '{value}' is not a number"
        if not lo <= number <= hi:
            return f"{col} {number:g} is outside {lo}–{hi}"
    return None


def delete_all() -> int:
    """Empty the table. Returns how many readings were removed."""
    with Session() as s:
        n = s.execute(delete(Reading)).rowcount
        s.commit()
        return n


# ── 2 · Ask: what is loaded, the raw rows, one day, the worst days ─────────────────────────────────
def stats() -> dict:
    """How many readings are loaded, and from when to when."""
    with Session() as s:
        n = s.scalar(select(func.count()).select_from(Reading))
        first, last = s.scalar(select(func.min(Reading.timestamp))), s.scalar(select(func.max(Reading.timestamp)))
    if not n:
        return {"readings": 0, "from": None, "to": None, "days": 0}
    return {"readings": n, "from": first.isoformat(timespec="minutes"), "to": last.isoformat(timespec="minutes"),
            "days": (last.date() - first.date()).days + 1}


def get_readings(start: datetime, end: datetime) -> list:
    """The raw rows from start (included) to end (not included) — at most MAX_DAYS at a time."""
    if end <= start:
        raise ValueError("end must be after start")
    if end - start > timedelta(days=MAX_DAYS):
        raise ValueError(f"ask for at most {MAX_DAYS} days at a time")
    with Session() as s:
        rows = s.scalars(select(Reading).where(Reading.timestamp >= start, Reading.timestamp < end).order_by(Reading.timestamp))
        return [{"timestamp": r.timestamp.isoformat(timespec="minutes"), "load_kw": r.load_kw, "solar_kw": r.solar_kw,
                 "ambient_c": r.ambient_c, "irradiance_wm2": r.irradiance_wm2} for r in rows]


def loading_pct(r: dict) -> float:
    """How full the transformer is: rooftop solar supplies part of the load, so TR-MAIN carries only the rest."""
    return 100 * max(r["load_kw"] - r["solar_kw"], 0) / PF / RATING_KVA


def status(pct: float) -> str:
    return "OVERLOAD" if pct > 100 else "HIGH" if pct > 80 else "NORMAL"


def summary(day: date) -> dict:
    """One day in numbers: peak load, energy used and made, the transformer's peak loading and its status."""
    start = datetime.combine(day, datetime.min.time())
    rows = get_readings(start, start + timedelta(days=1))
    if not rows:
        raise NotFound(f"no readings for {day}")
    peak = max(rows, key=lambda r: r["load_kw"])
    worst = max(rows, key=loading_pct)
    pct = round(loading_pct(worst), 1)
    return {"day": str(day), "readings": len(rows),
            "peak_load_kw": peak["load_kw"], "peak_load_time": peak["timestamp"][11:16],
            "load_kwh": round(sum(r["load_kw"] for r in rows) * 0.25),       # each reading covers 15 min = 0.25 h
            "solar_kwh": round(sum(r["solar_kw"] for r in rows) * 0.25),
            "peak_loading_pct": pct, "peak_loading_time": worst["timestamp"][11:16], "status": status(pct),
            "max_air_c": max(r["ambient_c"] for r in rows)}


def peak_days(top: int = 5) -> list:
    """The `top` days when the transformer worked hardest, highest loading first."""
    with Session() as s:
        rows = [{"timestamp": r.timestamp, "load_kw": r.load_kw, "solar_kw": r.solar_kw, "ambient_c": r.ambient_c}
                for r in s.scalars(select(Reading))]
    best = {}
    for r in rows:
        d = r["timestamp"].date()
        if d not in best or loading_pct(r) > loading_pct(best[d]):
            best[d] = r
    ranked = sorted(best.values(), key=loading_pct, reverse=True)[:top]
    return [{"day": str(r["timestamp"].date()), "peak_loading_pct": round(loading_pct(r), 1),
             "time": r["timestamp"].strftime("%H:%M"), "status": status(loading_pct(r)), "air_c": r["ambient_c"]} for r in ranked]
