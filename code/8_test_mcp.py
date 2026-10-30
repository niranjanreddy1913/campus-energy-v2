"""Part 3 — call every tool of the RUNNING MCP server, the way Cursor or any AI app does, and print every result.
Start the MCP server first:   python 6_mcp_server.py http          (port 8002)
Then, in a second terminal:   python 8_test_mcp.py
If the readings API is running too (python 3_readings_api.py, port 8001), it also checks REST and MCP give the same answer.
MCP server on another port?   MCP_URL=http://127.0.0.1:8012/mcp python 8_test_mcp.py"""
import asyncio
import json
import os
import sys

import httpx
from mcp import Client

MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:8002/mcp")     # where 6_mcp_server.py http runs
REST_URL = os.environ.get("API_URL", "http://127.0.0.1:8001")         # where 3_readings_api.py runs (optional here)


def reason(text):
    """The useful line of a refusal: ours, or pydantic's "Input should be …"."""
    lines = [l.strip() for l in text.splitlines()]
    return next((l.split(" [type")[0] for l in lines if l.startswith("Input should")), lines[0])


async def main():
    async with Client(MCP_URL) as ai:
        if ai.server_info.name != "campus-energy-v2":                   # make sure it's OUR server on that port
            return f"✗ The MCP server at {MCP_URL} is '{ai.server_info.name}', not campus-energy-v2. Start ours:  python 6_mcp_server.py http"
        print(f"Connected to MCP server '{ai.server_info.name}' at {MCP_URL}\n")

        # 1. An AI app first ASKS what tools exist (tools/list). REST has no such question — a person reads /docs.
        tools = (await ai.list_tools()).tools
        print(f"1 · tools/list → {len(tools)} tools: {', '.join(t.name for t in tools)}")

        async def call(name, args, short=200):
            r = await ai.call_tool(name, args)                          # tools/call
            if r.is_error:
                out = f"isError=True   {reason(r.content[0].text)}"
            else:
                data = [json.loads(c.text) for c in r.content]          # a list comes back as several items
                if len(data) == 1 and name not in ("peak_days", "get_readings"):   # those two always answer with a list
                    data = data[0]
                out = f"isError=False  {json.dumps(data, ensure_ascii=False)[:short]}"
            print(f"   {name}({', '.join(f'{k}={v!r}' for k, v in args.items())})".ljust(64) + f" → {out}")
            return r

        print("\n2 · The calculator (Part 1's logic)")
        await call("calculate", {"a": 12, "b": 3, "op": "div"})
        await call("calculate", {"a": 1, "b": 0, "op": "div"})          # our function refused it
        await call("calculate", {"a": 2, "b": 3, "op": "pow"})          # the schema refused it — our code never ran

        print("\n3 · The readings (Part 2's logic, the same readings.db the REST API filled)")
        await call("readings_stats", {})
        summary = await call("day_summary", {"day": "2026-03-23"})
        await call("peak_days", {"top": 3}, 300)
        await call("get_readings", {"start": "2026-03-23T12:00", "end": "2026-03-23T12:30"})

        print("\n4 · Refused, with a reason")
        await call("day_summary", {"day": "2026-05-01"})                # no data that day
        await call("get_readings", {"start": "2026-02-01T00:00", "end": "2026-03-01T00:00"})   # more than 7 days
        await call("peak_days", {"top": 0})                             # 1–31 only

        print("\n5 · Same question, two doors")
        try:
            rest = httpx.get(f"{REST_URL}/summary", params={"day": "2026-03-23"}, timeout=5).json()
            mcp_answer = json.loads(summary.content[0].text)
            print(f"   REST GET {REST_URL}/summary?day=2026-03-23 → {rest.get('peak_loading_pct')} % {rest.get('status')}")
            print(f"   MCP  day_summary(day='2026-03-23')                 → {mcp_answer['peak_loading_pct']} % {mcp_answer['status']}")
            print("   ✓ the same answer — one function, two doors" if rest == mcp_answer else "   ✗ they differ")
        except httpx.ConnectError:
            print(f"   (start the readings API too — python 3_readings_api.py — to compare REST and MCP here)")

try:                                                                    # is anything listening? (one clear line, not a traceback)
    httpx.get(MCP_URL, timeout=3)
except httpx.ConnectError:
    sys.exit(f"✗ Nothing is running at {MCP_URL}. Start the MCP server first:  python 6_mcp_server.py http")
problem = asyncio.run(main())
if problem:
    sys.exit(problem)
