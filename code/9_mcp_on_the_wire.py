"""Part 3 — what an MCP client really sends: four JSON-RPC messages, each one a plain HTTP POST to /mcp.
8_test_mcp.py hid them inside Client(...). Here we type them ourselves, as Postman or curl would.
Start the MCP server first:   python 6_mcp_server.py http          (port 8002)
Then, in a second terminal:   python 9_mcp_on_the_wire.py"""
import json
import os
import sys

import httpx

MCP_URL = os.environ.get("MCP_URL", "http://127.0.0.1:8002/mcp")
HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def post(message, session=None):
    """One MCP message = one HTTP POST of JSON-RPC. The answer comes back as JSON or as one server-sent event."""
    r = httpx.post(MCP_URL, json=message, headers=HEADERS | ({"mcp-session-id": session} if session else {}), timeout=30)
    body = r.text.strip()
    if body.startswith(("event:", "data:")):
        body = next(line[5:] for line in body.splitlines() if line.startswith("data:"))
    return r, (json.loads(body) if body else None)


def show(step, message, reply):
    print(f"\n{step}  →  {json.dumps(message)[:110]}")
    print(f"     ←  {json.dumps(reply, ensure_ascii=False)[:220] if reply else '(no body — a notification gets no answer)'}")


try:
    hello = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "mgit-v2", "version": "1"}}}
    r, reply = post(hello)
except httpx.ConnectError:
    sys.exit(f"✗ Nothing is running at {MCP_URL}. Start the MCP server first:  python 6_mcp_server.py http")
name = reply["result"]["serverInfo"]["name"]
if name != "campus-energy-v2":                                         # make sure it's OUR server on that port
    sys.exit(f"✗ The MCP server at {MCP_URL} is '{name}', not campus-energy-v2. Start ours:  python 6_mcp_server.py http")
session = r.headers["mcp-session-id"]                                  # in the HEADERS, not the body
show("① initialize", hello, reply)
print(f"     session id (response header mcp-session-id): {session}")

ready = {"jsonrpc": "2.0", "method": "notifications/initialized"}      # no "id": a notification, not a question
r, reply = post(ready, session)
show("② notifications/initialized", ready, reply)
print(f"     HTTP {r.status_code}")

ask = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
r, reply = post(ask, session)
show("③ tools/list", ask, reply)
for t in reply["result"]["tools"]:                                     # the JSON Schema comes from the type hints in 6_mcp_server.py
    print(f"     {t['name']:<15} needs {t['inputSchema'].get('required', [])}")

call = {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "day_summary", "arguments": {"day": "2026-03-23"}}}
r, reply = post(call, session)
show("④ tools/call", call, reply)
answer = json.loads(reply["result"]["content"][0]["text"])
print(f"     result: {answer['day']} peak loading {answer['peak_loading_pct']} % → {answer['status']}")

r, reply = post(ask)                                                   # forget the session id
print(f"\nWithout the session id  →  HTTP {r.status_code}: {reply['error']['message']}")
