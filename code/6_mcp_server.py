"""Part 3 — the SAME logic as both REST APIs, published as MCP tools for AI apps (Cursor, Claude, VS Code, your own agent).
What we ADD is this one file and one library (pip install mcp). calculator.py, readings.py and db.py don't change.
    REST (1_ and 3_)                         MCP (this file)
    app = FastAPI(...)                       mcp = MCPServer(...)
    @app.get("/summary")                     @mcp.tool()             — a tool has a NAME, not a URL and a method
    type hints → /docs, for a person         type hints → a JSON Schema the AI app reads (tools/list)
    raise HTTPException(404, ...)            raise ToolError(...)    — the AI app gets isError: true and the reason
Run over HTTP (Cursor, the UI, the scripts 8_–10_):          python 6_mcp_server.py           → http://127.0.0.1:8002/mcp
                                       (the same, spelled out:  python 6_mcp_server.py http;  another port: python 6_mcp_server.py http 8012)
Run over stdio (the AI app starts it itself, no port):      python 6_mcp_server.py stdio     — only cursor_mcp_stdio.json uses this"""
import sys
import os
from datetime import date, datetime
from typing import Annotated, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field

import calculator
import readings

mcp = MCPServer("campus-energy-v2",
                instructions="A calculator, and the campus substation's readings (1 Feb – 31 Mar 2026) for transformer TR-MAIN.",
                log_level="WARNING")                   # quiet: only problems are printed


def refused_as_tool_error(fn, *args):
    """Call the same function REST calls. Its refusal becomes a ToolError — the MCP way to say "no, because …".
    (Any other exception reaches the AI app only as "Error executing tool", without the reason.)"""
    try:
        return fn(*args)
    except (ValueError, readings.NotFound) as e:          # ÷ 0, a 30-day range, a day with no readings
        raise ToolError(str(e))


# ── From Part 1: GET / POST /calculate  →  the tool "calculate" ────────────────────────────────────
# The docstring is the tool's description: it is the ONLY thing the AI knows about what the tool does.
@mcp.tool()
def calculate(a: Annotated[float, Field(description="the first number")],
              b: Annotated[float, Field(description="the second number")],
              op: Annotated[Literal["add", "sub", "mul", "div"], Field(description="add, sub, mul or div")]) -> dict:
    """Add, subtract, multiply or divide two numbers."""
    return {"a": a, "b": b, "op": op, "result": refused_as_tool_error(calculator.calculate, a, b, op)}


# ── From Part 2: the four READ endpoints become four tools ─────────────────────────────────────────
# POST /readings/upload and DELETE /readings are NOT tools: they change data, and that stays with a person.
@mcp.tool()
def readings_stats() -> dict:
    """How many substation readings are loaded, and from when to when. Ask this first if unsure what data exists."""
    return readings.stats()


@mcp.tool()
def get_readings(start: Annotated[datetime, Field(description="from this moment, e.g. 2026-03-23T12:00")],
                 end: Annotated[datetime, Field(description="up to this moment (not included), e.g. 2026-03-23T13:00")]) -> list:
    """The raw 15-minute readings (load kW, solar kW, air °C, sunlight W/m²) between two moments — at most 7 days."""
    return refused_as_tool_error(readings.get_readings, start, end)


@mcp.tool()
def day_summary(day: Annotated[date, Field(description="the day, YYYY-MM-DD, e.g. 2026-03-23")]) -> dict:
    """One day for transformer TR-MAIN: peak load, energy used and from solar, peak loading % and status (NORMAL / HIGH / OVERLOAD)."""
    return refused_as_tool_error(readings.summary, day)


@mcp.tool()
def peak_days(top: Annotated[int, Field(ge=1, le=31, description="how many days, 1–31")] = 5) -> list:
    """The days when transformer TR-MAIN worked hardest, highest loading first."""
    return readings.peak_days(top)



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        print("MCP server campus-energy-v2 · 5 tools · stdio", file=sys.stderr)
        mcp.run()
    else:
        port = int(os.environ.get("PORT", sys.argv[2] if len(sys.argv) > 2 else 8002))

        hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

        if hostname:
            security = TransportSecuritySettings(
                allowed_hosts=[hostname, f"{hostname}:*"]
            )
        else:
            security = None

        print(f"MCP server running on port {port}", file=sys.stderr)

        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=port,
            transport_security=security
        )