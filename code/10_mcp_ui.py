"""Part 3 — a Streamlit UI for ANY MCP server: it lists the tools (tools/list) and lets you call one (tools/call) from a form.
It builds every form from the tool's JSON Schema, so it knows nothing about our tools in advance — like Cursor, but YOU pick the tool.
Start the MCP server first:   python 6_mcp_server.py http          (port 8002)
Then:                         streamlit run 10_mcp_ui.py           → http://localhost:8501
MCP server on another port?   MCP_URL=http://127.0.0.1:8012/mcp streamlit run 10_mcp_ui.py"""
import asyncio
import json
import os
from datetime import date, datetime

import httpx
import streamlit as st
from mcp import Client

st.set_page_config(page_title="MCP tools", page_icon="🔌", layout="wide")


# ── talking to the server: the same two messages Cursor sends ──────────────────────────────────────
def run(coro):
    return asyncio.run(coro)


async def discover(url):
    """initialize + tools/list: the server's name and every tool's name, description and JSON Schema."""
    async with Client(url) as client:
        return client.server_info.name, (await client.list_tools()).tools


async def call(url, name, args):
    """tools/call: run one tool. A list comes back as several content items, one per element."""
    async with Client(url) as client:
        r = await client.call_tool(name, args)
    items = []
    for c in r.content:
        try:
            items.append(json.loads(c.text))
        except (ValueError, AttributeError):
            items.append(getattr(c, "text", str(c)))
    return r.is_error, items


def reason(text):
    """The useful line of a refusal: ours, or pydantic's "Input should be …"."""
    lines = [l.strip() for l in str(text).splitlines()]
    return next((l.split(" [type")[0] for l in lines if l.startswith("Input should")), lines[0])


# ── one form field per argument, chosen from its JSON Schema ───────────────────────────────────────
def field(name, schema, required, key):
    """Return the value the user entered, or None to leave the argument out (the tool's default is used)."""
    kind, fmt, default = schema.get("type"), schema.get("format"), schema.get("default")
    label = f"{name}{' *' if required else ''}"
    help_ = schema.get("description", "")
    if "enum" in schema:
        return st.selectbox(label, schema["enum"], help=help_, key=key)
    if kind == "integer":
        return int(st.number_input(label, value=int(default if default is not None else schema.get("minimum", 0)),
                                   min_value=schema.get("minimum"), max_value=schema.get("maximum"), step=1, help=help_, key=key))
    if kind == "number":
        return float(st.number_input(label, value=float(default or 0), help=help_, key=key))
    if kind == "boolean":
        return st.checkbox(label, value=bool(default), help=help_, key=key)
    if fmt == "date":
        return st.date_input(label, value=date(2026, 3, 23), help=help_, key=key).isoformat()
    if fmt == "date-time":
        text = st.text_input(label, value="2026-03-23T12:00" if "start" in name else "2026-03-23T13:00", help=help_, key=key)
        return text.strip() or None
    if kind in ("object", "array"):
        text = st.text_area(label + " (JSON)", value=json.dumps(default) if default is not None else "", help=help_, key=key)
        return json.loads(text) if text.strip() else None
    text = st.text_input(label, value=str(default or ""), help=help_, key=key)
    return text if text or required else None


# ── the page ───────────────────────────────────────────────────────────────────────────────────────
st.title("🔌 MCP tools")
st.caption("Every tool the server offers, read with tools/list — and a form to call it with tools/call. The forms are built from each tool's JSON Schema.")

with st.sidebar:
    url = st.text_input("MCP server URL", value=os.environ.get("MCP_URL", "http://127.0.0.1:8002/mcp"))
    if st.button("Connect / refresh", width="stretch") or "tools" not in st.session_state or st.session_state.get("url") != url:
        try:
            httpx.get(url, timeout=3)                        # is anything listening? (one clear line, not a traceback)
            st.session_state.server, st.session_state.tools = run(discover(url))
            st.session_state.url, st.session_state.error = url, None
        except httpx.ConnectError:
            st.session_state.tools, st.session_state.error = [], f"Nothing is running at {url}. Start it:  python 6_mcp_server.py http"
        except Exception as e:                               # e.g. not an MCP server at that address
            while hasattr(e, "exceptions"):
                e = e.exceptions[0]
            st.session_state.tools, st.session_state.error = [], f"Could not talk MCP to {url}: {e}"
    if st.session_state.get("error"):
        st.error(st.session_state.error)
    else:
        st.success(f"Connected to **{st.session_state.server}** · {len(st.session_state.tools)} tools")
    st.markdown("**The same server is used by** Cursor (`.cursor/mcp.json`) and Claude Code (`.mcp.json`).")

tools = st.session_state.get("tools", [])
if not tools:
    st.info("Start the MCP server, then press **Connect / refresh**.")
    st.stop()

# 1 · the list of tools — what Cursor shows under the server
st.subheader(f"1 · The tools ({len(tools)}) — from tools/list")
st.dataframe([{"tool": t.name,
               "inputs": ", ".join(f"{p}{'*' if p in t.input_schema.get('required', []) else ''}" for p in t.input_schema.get("properties", {})) or "—",
               "description": t.description} for t in tools], hide_index=True, width="stretch")
st.caption("\\* = required. The description is all an AI app knows about a tool — it chooses from it.")

# 2 · choose one, fill its form, call it
st.subheader("2 · Call a tool — tools/call")
left, right = st.columns([2, 3])
with left:
    chosen = st.radio("Tool", [t.name for t in tools], horizontal=True, key="tool")
    tool = next(t for t in tools if t.name == chosen)
    st.markdown(f"**{tool.name}** — {tool.description}")
    props, required = tool.input_schema.get("properties", {}), tool.input_schema.get("required", [])
    with st.form(f"form-{tool.name}"):
        args = {}
        for name, schema in props.items():
            value = field(name, schema, name in required, f"{tool.name}.{name}")
            if value is not None:
                args[name] = value
        if not props:
            st.caption("This tool takes no arguments.")
        go = st.form_submit_button(f"▶ Call {tool.name}", type="primary", width="stretch")
    with st.expander("Its JSON Schema (what the AI app reads)"):
        st.json(tool.input_schema)

with right:
    if go:
        is_error, items = run(call(url, tool.name, args))
        st.session_state.setdefault("history", []).insert(0, {"tool": tool.name, "arguments": json.dumps(args),
                                                               "isError": is_error, "answer": reason(items[0]) if is_error else json.dumps(items)[:90]})
        st.session_state.last = (tool.name, args, is_error, items)
    if "last" in st.session_state:
        name, sent, is_error, items = st.session_state.last
        st.markdown("**Sent** (the JSON-RPC message):")
        st.code(json.dumps({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": name, "arguments": sent}}, indent=2), language="json")
        if is_error:
            st.error(f"isError: true — {reason(items[0])}")
        else:
            st.success(f"isError: false — {len(items)} content item{'s' if len(items) != 1 else ''}")
            st.json(items[0] if len(items) == 1 else items)
    else:
        st.info("Fill the form and press **Call**. Try a refusal too: calculate with b = 0, or day_summary for 2026-05-01.")

# 3 · what you called this session
if st.session_state.get("history"):
    st.subheader("3 · Your calls")
    st.dataframe(st.session_state.history[:10], hide_index=True, width="stretch")
