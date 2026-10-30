"""Part 1 — the calculator as a REST API: two numbers and one operation in, the answer out, as JSON.
Run:   python 1_calculator_api.py     or   uvicorn 1_calculator_api:app --reload     (port 8000 busy? python 1_calculator_api.py 8010)
Open:  http://127.0.0.1:8000/docs        ← every endpoint, with "Try it out" — written by FastAPI from this file
Try:   http://127.0.0.1:8000/calculate?a=12&b=3&op=div"""
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import calculator

app = FastAPI(title="Calculator API", version="v2-part-1",
              description="Two numbers and one operation: add, sub, mul or div.")

Operation = Literal["add", "sub", "mul", "div"]          # only these four words — anything else is refused with 422


@app.get("/")
def home():
    return {"message": "Calculator API is running. Open /docs to try it."}


# ── 1 · GET: the inputs travel in the address ──────────────────────────────────────────────────────
@app.get("/calculate")
def calculate_get(a: float, b: float, op: Operation):
    """Calculate with the inputs in the URL: /calculate?a=12&b=3&op=div"""
    try:
        return {"a": a, "b": b, "op": op, "result": calculator.calculate(a, b, op)}
    except ValueError as e:                               # the function said no (divide by zero) → 400, with its reason
        raise HTTPException(status_code=400, detail=str(e))


# ── 2 · POST: the same calculation, the inputs in a JSON body ──────────────────────────────────────
class CalcRequest(BaseModel):
    """What the JSON body must contain. The same shape an MCP tool's arguments will have in Part 3."""
    a: float = Field(description="the first number", examples=[12])
    b: float = Field(description="the second number", examples=[3])
    op: Operation = Field(description="add, sub, mul or div", examples=["div"])


@app.post("/calculate")
def calculate_post(req: CalcRequest):
    """Calculate with the inputs in a JSON body: {"a": 12, "b": 3, "op": "div"}"""
    return calculate_get(req.a, req.b, req.op)            # one rule for both: GET and POST call the same code


if __name__ == "__main__":                       # python 1_calculator_api.py works too — from any folder; another port: python 1_calculator_api.py 8010
    import sys
    from pathlib import Path

    import uvicorn
    here = Path(__file__).resolve().parent
    uvicorn.run("1_calculator_api:app", app_dir=str(here), reload=True, reload_dirs=[str(here)],
                host="127.0.0.1", port=int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
