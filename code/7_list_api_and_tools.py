"""Part 3 — the two lists, read from the code itself: every REST endpoint of both APIs (what /docs shows a person)
and every MCP tool (what Cursor shows an AI app). Then which tool matches which endpoint — and which endpoints have none.
Run:  python 7_list_api_and_tools.py      (no server needed: it reads the three files directly)"""
import asyncio
import importlib

from mcp import Client

calc_api = importlib.import_module("1_calculator_api").app      # names starting with a digit: importlib, not `import`
read_api = importlib.import_module("3_readings_api").app
mcp = importlib.import_module("6_mcp_server").mcp

# ── 1. REST: method + URL, read from the same OpenAPI description that /docs draws ──────────────────
print("REST endpoints — for people and programs (/docs)")
for name, port, app in [("Calculator API", 8000, calc_api), ("Readings API", 8001, read_api)]:
    print(f"  {name}, http://127.0.0.1:{port}")
    for url, methods in app.openapi()["paths"].items():
        for method, op in methods.items():
            params = [p["name"] for p in op.get("parameters", [])] + (["body"] if "requestBody" in op else [])
            print(f"     {method.upper():<7}{url:<20}{', '.join(params) or '—'}")


# ── 2. MCP: name + description + JSON Schema, read with tools/list like any AI app ──────────────────
async def list_tools():
    async with Client(mcp) as client:
        return (await client.list_tools()).tools

tools = asyncio.run(list_tools())
print(f"\nMCP tools — for AI apps (Cursor lists these under 'campus-energy-v2', http://127.0.0.1:8002/mcp): {len(tools)} tools")
for t in tools:
    print(f"     {t.name:<16}{', '.join(t.input_schema.get('properties', {})) or '—':<14}{t.description}")

# ── 3. Same function, two doors ──────────────────────────────────────────────────────────────────────
SAME = [("GET  /calculate · POST /calculate", "calculate", "calculator.calculate"),
        ("GET  /readings/stats", "readings_stats", "readings.stats"),
        ("GET  /readings", "get_readings", "readings.get_readings"),
        ("GET  /summary", "day_summary", "readings.summary"),
        ("GET  /peak-days", "peak_days", "readings.peak_days"),
        ("POST /readings/upload", "—", "readings.load_csv     (changes data: REST only, done by a person)"),
        ("DELETE /readings", "—", "readings.delete_all   (changes data: REST only, done by a person)"),
        ("GET  /   (both APIs)", "—", "a welcome message; an AI app asks tools/list instead")]
print("\nThe same function behind both doors:")
for rest, tool, fn in SAME:
    print(f"     {rest:<34}↔  {tool:<16}{fn}")
