"""Build the v2 student page, index.html: REST first (Part 1 calculator, Part 2 readings), then MCP (Part 3, next).
Every code box is read from the real file and every output is captured by running the real program, so the page can't drift.
    python tools/build_page.py          (from v2/; set MGIT_PY to the Python that has the packages)"""
import html
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from contextlib import contextmanager
from pathlib import Path

V2 = Path(__file__).resolve().parents[1]
PY = os.environ.get("MGIT_PY", sys.executable)
esc = html.escape
CODE = "code"                       # everything students use is in this one folder


# ── pieces of a page (the same look as v1's pages) ─────────────────────────────────────────────────
def run(folder, script, *args, api_url=None, mcp_url=None):
    env = dict(os.environ, PYTHONWARNINGS="ignore", **({"API_URL": api_url} if api_url else {}), **({"MCP_URL": mcp_url} if mcp_url else {}))
    r = subprocess.run([PY, script, *args], cwd=V2 / folder, capture_output=True, text=True, timeout=300, env=env)
    if r.returncode != 0:
        raise SystemExit(f"✗ {folder}/{script} failed:\n{r.stderr[-2000:]}")
    print(f"   ran {folder}/{script}")
    return "\n".join(l for l in r.stdout.splitlines() if not l.startswith("HTTP Request:")).rstrip()


@contextmanager
def server(script, *args):
    """Start one of the servers on a free port, as a student does in their first terminal, and stop it afterwards."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    p = subprocess.Popen([PY, script, *args, str(port)], cwd=V2 / CODE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                urllib.request.urlopen(url + "/", timeout=1)
                break
            except urllib.error.HTTPError:                # it answered (the MCP server says 404 to GET /): it's up
                break
            except OSError:
                time.sleep(0.2)
        yield url
    finally:
        p.terminate()
        p.wait(timeout=20)


def code(path, lang="python"):
    text = (V2 / path).read_text()
    return (f'<div class="code" data-file="{esc(path)}" data-lang="{lang}" data-name="{esc(Path(path).name)}">\n'
            f'<script type="text/x-{lang}">\n{text.replace("</script", "<\\/script")}\n</script>\n</div>')


def cmd(commands):
    return f'<div class="code" data-lang="bash" data-name="terminal">\n<script type="text/x-bash">\n{commands}\n</script>\n</div>'


def image(name, caption):
    """A screenshot from assets/img/screens/ — every one is a real run (see the 'Testing screens' step)."""
    assert (V2 / "assets/img/screens" / name).exists(), name
    return (f'<figure class="shot"><img src="assets/img/screens/{esc(name)}" alt="{esc(caption)}" loading="lazy">'
            f'<figcaption>{caption}</figcaption></figure>')


def output(text, caption="Output"):
    return f'<p class="out-label">▶ {esc(caption)}</p><div class="output">{esc(text)}</div>'


def flow(boxes, caption):
    n = len(boxes)
    w = min(150, (740 - (n - 1) * 34) // n)
    x0 = (776 - (n * w + (n - 1) * 34)) // 2
    parts = [f'<svg viewBox="0 0 776 110" role="img" aria-label="{esc(caption)}"><defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" '
             'markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="head" d="M0,0 L10,5 L0,10 z"/></marker></defs>']
    for i, (title, sub, hot) in enumerate(boxes):
        x = x0 + i * (w + 34)
        parts.append(f'<rect class="{"soft-acc" if hot else "box"}" x="{x}" y="20" width="{w}" height="64" rx="10"/>')
        parts.append(f'<text class="b" x="{x + w / 2}" y="47" text-anchor="middle">{esc(title)}</text>')
        parts.append(f'<text class="sm" x="{x + w / 2}" y="67" text-anchor="middle">{esc(sub)}</text>')
        if i < n - 1:
            parts.append(f'<path class="line" d="M{x + w + 2} 52 L{x + w + 30} 52" marker-end="url(#ah)"/>')
    return f'<figure class="diagram"><div class="scroll">{"".join(parts)}</svg></div><figcaption>{caption}</figcaption></figure>'


def callout(kind, text, icon=None):
    icon = icon or {"tip": "✅", "warn": "⚠️", "info": "💡", "ee": "⚡"}[kind]
    return f'<div class="callout {kind}"><span class="ico">{icon}</span><div><p>{text}</p></div></div>'


def table(head, rows):
    h = "".join(f"<th>{c}</th>" for c in head)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="table-wrap"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'


def try_it(items):
    return '<div class="try"><h4>✍️ Try it yourself</h4><ol>' + "".join(f"<li>{i}</li>" for i in items) + "</ol></div>"


def learn(items):
    return '<div class="learn"><h4>What you will learn</h4><ul>' + "".join(f"<li>{i}</li>" for i in items) + "</ul></div>"


def problem(story, given, find, rules):
    return (f'<div class="problem"><h4>🎯 Problem statement</h4><p>{story}</p><dl class="gf"><dt>Given</dt><dd>{given}</dd>'
            f'<dt>Find</dt><dd>{find}</dd><dt>Rules</dt><dd>{rules}</dd></dl></div>')


def quiz(questions):
    return ('<p class="muted">Check yourself — answers are explained after you submit.</p><div class="quiz"><script type="application/json">'
            + json.dumps(questions, ensure_ascii=False, indent=1) + "</script></div>")


C = lambda t: f"<code>{t}</code>"     # noqa: E731


# ── the sections ───────────────────────────────────────────────────────────────────────────────────
def sections():
    calc_fn = run(CODE, "calculator.py")
    with server("1_calculator_api.py") as url:
        calc_test = run(CODE, "2_test_calculator.py", api_url=url).replace(url, "http://127.0.0.1:8000")
    with server("3_readings_api.py") as url:
        read_test = run(CODE, "5_test_readings.py", api_url=url).replace(url, "http://127.0.0.1:8001")
    lists = run(CODE, "7_list_api_and_tools.py")
    with server("3_readings_api.py") as rest, server("6_mcp_server.py", "http") as m:
        mcp_test = run(CODE, "8_test_mcp.py", api_url=rest, mcp_url=m + "/mcp").replace(m, "http://127.0.0.1:8002").replace(rest, "http://127.0.0.1:8001")
        wire = run(CODE, "9_mcp_on_the_wire.py", mcp_url=m + "/mcp").replace(m, "http://127.0.0.1:8002")
    wire = "\n".join(l if "session id" not in l else l[:l.rindex(":") + 2] + "3f9c… (a new one each time)" for l in wire.splitlines())
    return [
        dict(title="Today's plan: REST first, then MCP", body="".join([
            "<p>We build two small REST APIs, then — in Part 3 — open the <em>same</em> logic to AI apps such as Cursor with MCP. "
            "Each part adds one idea:</p>",
            table(["Part", "What we build", "The new idea"], [
                ["<b>1 · Calculator API</b>", "Two numbers and one operation in, the answer out", "An API: GET and POST, inputs, JSON, <code>/docs</code>, status codes 200 / 400 / 422"],
                ["<b>2 · Readings API</b>", "Upload a CSV of 5,664 substation readings <em>through the API</em>, then ask questions", "A file upload, checking every row, a database, query endpoints, 404"],
                ["<b>3 · MCP</b>", "The same two APIs as MCP tools, connected to Cursor", "Tools an AI app can discover and call — REST and MCP side by side"]]),
            flow([("calculator.py", "+ readings.py", True), ("1_ · 3_ …_api.py", "REST: /docs", False),
                  ("6_mcp_server.py", "MCP: tools (Part 3)", True), ("Browser · Cursor", "two kinds of client", False)],
                 "<b>Write the logic once, give it many doors.</b> The logic files have no FastAPI in them, so in Part 3 the MCP server imports the same functions."),
            callout("info", "<strong>The rule for the whole workshop:</strong> logic in plain Python functions (<code>calculator.py</code>, "
                            "<code>readings.py</code>); an API file (<code>1_calculator_api.py</code>, <code>3_readings_api.py</code>) only receives requests, calls a function and returns its answer."),
            "<p><strong>Everything is in one folder, <code>code/</code>.</strong> The numbers are the order: <code>1_</code> … <code>5_</code> are what you run. "
            "<code>calculator.py</code>, <code>readings.py</code> and <code>db.py</code> have no number because the APIs <em>import</em> them — "
            "and Python can't <code>import</code> a name that starts with a digit.</p>",
            table(["File", "What it is", "How you use it"], [
                ["<code>1_calculator_api.py</code>", "Part 1: the calculator REST API, on port 8000", "<code>python 1_calculator_api.py</code>"],
                ["<code>2_test_calculator.py</code>", "Part 1: every case, with the replies", "<code>python 2_test_calculator.py</code> (second terminal, API running)"],
                ["<code>3_readings_api.py</code>", "Part 2: the readings REST API (upload + questions), on port 8001", "<code>python 3_readings_api.py</code>"],
                ["<code>4_upload_csv.py</code>", "Part 2: uploads the CSV to the running API", "<code>python 4_upload_csv.py</code> (second terminal)"],
                ["<code>5_test_readings.py</code>", "Part 2: every endpoint, including refusals", "<code>python 5_test_readings.py</code> (second terminal, API running)"],
                ["<code>calculator.py</code>, <code>readings.py</code>, <code>db.py</code>", "The logic and the database — imported by the APIs", "Read them; <code>python calculator.py</code> runs a quick check"],
                ["<code>6_mcp_server.py</code>", "Part 3: the same logic as 5 MCP tools, on port 8002", "<code>python 6_mcp_server.py http</code>"],
                ["<code>7_list_api_and_tools.py</code>", "Part 3: the REST endpoints and the MCP tools, side by side", "<code>python 7_list_api_and_tools.py</code>"],
                ["<code>8_test_mcp.py</code>", "Part 3: every tool of the running MCP server", "<code>python 8_test_mcp.py</code> (second terminal, MCP running)"],
                ["<code>9_mcp_on_the_wire.py</code>", "Part 3: the four JSON-RPC messages, by hand", "<code>python 9_mcp_on_the_wire.py</code> (MCP running)"],
                ["<code>10_mcp_ui.py</code>", "Part 3: a Streamlit UI — the list of tools, and a form to call each one", "<code>streamlit run 10_mcp_ui.py</code> (MCP running)"],
                ["<code>cursor_mcp.json</code>, <code>cursor_mcp_stdio.json</code>", "Part 3: connect Cursor to the MCP server", "Copy one to <code>.cursor/mcp.json</code>"],
                ["<code>campus_feb_mar_2026.csv</code>, <code>readings_with_problems.csv</code>", "The data to upload: 5,664 rows, and 9 rows with mistakes", "Upload through the API"]]),
            table(["Server", "Port", "Start it"], [
                ["Calculator API (Part 1)", "<b>8000</b>", "<code>python 1_calculator_api.py</code>"],
                ["Readings API (Part 2)", "<b>8001</b>", "<code>python 3_readings_api.py</code>"],
                ["MCP server (Part 3)", "<b>8002</b>", "<code>python 6_mcp_server.py http</code>"]]),
            "<p><strong>Set up once</strong> (from the <code>v2/</code> folder):</p>",
            cmd("pip install -r requirements.txt"),
            code("requirements.txt", "text"),
        ])),
        dict(title="Part 1 · Step 1 — The logic: calculator.py", steps=["Code", "Run"], body="".join([
            learn(["A function that does one job and refuses what it can't do (<code>ValueError</code>)",
                   "Why the logic lives in its own file, with no web code"]),
            problem("Everyone needs quick calculations, but a script on one laptop helps only the person at that keyboard.",
                    "two numbers and an operation", "the answer, available to any program on the network",
                    "only add, sub, mul, div; dividing by zero is refused with a clear reason"),
            code(f"{CODE}/calculator.py"),
            cmd("cd code\npython calculator.py"),
            output(calc_fn),
        ])),
        dict(title="Part 1 · Step 2 — The calculator as a REST API: 1_calculator_api.py", steps=["Concept", "Code", "Run", "Open /docs"], body="".join([
            learn(["<code>app = FastAPI()</code> and <code>@app.get(\"/calculate\")</code>: a function gets a web address",
                   "GET (inputs in the address) and POST (inputs in a JSON body) — the same answer",
                   "<code>Literal[...]</code> and a pydantic class: the API refuses bad input before your code runs"]),
            flow([("Browser / program", "a request", False), ("GET /calculate?…", "or POST + JSON", False), ("1_calculator_api.py", "FastAPI", True),
                  ("calculator.py", "calculate()", False), ("JSON", "the answer", False)],
                 "<b>How a request travels:</b> FastAPI checks the inputs, calls our function and sends back JSON."),
            code(f"{CODE}/1_calculator_api.py"),
            cmd("cd code\npython 1_calculator_api.py          # or: uvicorn 1_calculator_api:app --reload   ·   port 8000 busy? python 1_calculator_api.py 8010"),
            try_it(["Open <a href=\"http://127.0.0.1:8000/calculate?a=12&amp;b=3&amp;op=div\">http://127.0.0.1:8000/calculate?a=12&amp;b=3&amp;op=div</a> — the answer is JSON",
                    "Open <a href=\"http://127.0.0.1:8000/docs\">/docs</a>: FastAPI wrote it from <code>1_calculator_api.py</code>. Click <b>GET /calculate</b> → <b>Try it out</b> → <b>Execute</b>",
                    "In <b>POST /calculate</b>, edit the JSON body to <code>{\"a\": 7, \"b\": 6, \"op\": \"mul\"}</code> and execute",
                    "Try <code>op=pow</code>, then <code>b=0</code> with <code>div</code>: two different refusals — see the next step"]),
        ])),
        dict(title="Part 1 · Step 3 — Test it, and read the status codes", steps=["Run", "Observe"], body="".join([
            code(f"{CODE}/2_test_calculator.py"),
            "<p>Leave the API running and open a <b>second terminal</b>. The test calls the running API over HTTP, as any other program would:</p>",
            cmd("cd code\npython 2_test_calculator.py"),
            output(calc_test),
            table(["Status", "Means", "Who said no"], [
                ["<b>200</b> OK", "Here is the answer", "—"],
                ["<b>400</b> Bad request", "The request was fine, but the values can't be done (1 ÷ 0)", "<b>Our function</b> (<code>ValueError</code> → <code>HTTPException</code>)"],
                ["<b>422</b> Unprocessable", "The request broke the endpoint's rules (op=pow, a=twelve, b missing)", "<b>FastAPI</b>, before our code ran"]]),
            callout("tip", "<strong>Why GET and POST both?</strong> GET is easy to try in a browser. POST with a JSON body is how most programs send "
                           "inputs — and it's the exact shape an MCP tool's arguments will have in Part 3: <code>{\"a\": 12, \"b\": 3, \"op\": \"div\"}</code>."),
        ])),
        dict(title="Part 2 · Step 1 — The data, and where it's kept", steps=["Concept", "Data", "Code"], body="".join([
            learn(["A CSV of 5,664 readings: one every 15 minutes for two months", "A database table (SQLite) described as a Python class"]),
            problem("The substation's meter readings arrive as a CSV file. People need answers — <em>was the transformer overloaded on 23 March?</em> "
                    "— without opening a spreadsheet.",
                    "<code>campus_feb_mar_2026.csv</code> (5,664 rows) and <code>readings_with_problems.csv</code> (9 rows with mistakes), in <code>code/</code>",
                    "an API that loads the file when it's <em>uploaded</em>, keeps it in a database and answers questions about it",
                    "check every row; report what was refused and why; never store a half-checked file"),
            table(["Column", "Meaning", "Range in the data"], [
                ["<code>timestamp</code>", "When the reading was taken (every 15 min)", "1 Feb – 31 Mar 2026"],
                ["<code>load_kw</code>", "Power the whole campus is using", "162 – 891 kW"],
                ["<code>solar_kw</code>", "Power the rooftop solar makes", "0 (night) – 384 kW"],
                ["<code>ambient_c</code>", "Air temperature", "11.5 – 38.9 °C"],
                ["<code>irradiance_wm2</code>", "Sunlight on the panels", "0 – 1,049 W/m²"]]),
            code(f"{CODE}/db.py"),
            callout("info", "The readings are <b>generated, not real</b> (fixed seed — everyone gets the same numbers), with no client or personal data."),
        ])),
        dict(title="Part 2 · Step 2 — The logic: readings.py", steps=["Load", "Ask"], body="".join([
            learn(["Checking every row of an upload: columns, dates, numbers, physical limits, duplicates",
                   "Answering questions from the database: what's loaded, one day, the worst days",
                   "Transformer loading %: (load − solar) ÷ 0.93 ÷ 630 kVA → NORMAL / HIGH (&gt; 80 %) / OVERLOAD (&gt; 100 %)"]),
            code(f"{CODE}/readings.py"),
            callout("tip", "<strong>Two kinds of \"no\".</strong> <code>ValueError</code> means the request can't be done (a 30-day range, a wrong file) "
                           "and <code>NotFound</code> means the data isn't there (a day with no readings). The API turns them into 400 and 404."),
        ])),
        dict(title="Part 2 · Step 3 — The readings API: 3_readings_api.py", steps=["Endpoints", "Code", "Run"], body="".join([
            table(["Method", "Endpoint", "Inputs", "What it does"], [
                ["POST", "<code>/readings/upload</code>", "a CSV file; <code>replace</code> (true / false)", "Load the file — every row checked. Returns a report"],
                ["GET", "<code>/readings/stats</code>", "—", "How many readings are loaded, from when to when"],
                ["GET", "<code>/readings</code>", "<code>start</code>, <code>end</code>", "The raw rows — at most 7 days at a time"],
                ["GET", "<code>/summary</code>", "<code>day</code>", "One day: peak load, energy, solar, peak loading %, status"],
                ["GET", "<code>/peak-days</code>", "<code>top</code> (1–31)", "The days the transformer worked hardest"],
                ["DELETE", "<code>/readings</code>", "—", "Remove everything — to start again"]]),
            code(f"{CODE}/3_readings_api.py"),
            cmd("cd code\npython 3_readings_api.py            # port 8001   ·   or: uvicorn 3_readings_api:app --reload --port 8001"),
            callout("info", "<strong>Two APIs, two ports.</strong> The calculator uses <b>8000</b> and the readings API uses <b>8001</b>, so both can run at "
                            "the same time. Open the readings API at <a href=\"http://127.0.0.1:8001/docs\">http://127.0.0.1:8001/docs</a>. "
                            "<code>4_upload_csv.py</code> and <code>5_test_readings.py</code> use 8001 and check that they found the <em>Readings</em> API "
                            "before sending anything."),
        ])),
        dict(title="Part 2 · Step 4 — Load the data through the API", steps=["/docs", "A program", "curl"], body="".join([
            "<p>Three ways to send the same file to <code>POST /readings/upload</code>. Each one is a <em>client</em> of the API:</p>",
            try_it(["<b>In /docs:</b> open <a href=\"http://127.0.0.1:8001/docs\">:8001/docs</a> → <b>POST /readings/upload</b> → <b>Try it out</b> → "
                    "<b>Choose file</b> → <code>code/campus_feb_mar_2026.csv</code> → <b>Execute</b>. The report says <b>5,664 loaded, 0 refused</b>",
                    "Now upload <code>readings_with_problems.csv</code>: 3 loaded, 6 refused — read why, line by line",
                    "Upload the big file again with <code>replace = false</code>: 0 loaded, 5,664 already there — nothing is added twice",
                    "Then <b>GET /summary</b> with <code>2026-03-23</code> → 106.4 %, OVERLOAD"]),
            "<p><b>From a program</b> — the API must be running (in a second terminal):</p>",
            code(f"{CODE}/4_upload_csv.py"),
            cmd("cd code\npython 4_upload_csv.py\npython 4_upload_csv.py readings_with_problems.csv"),
            "<p><b>From the terminal</b> with curl:</p>",
            cmd('curl -F "file=@campus_feb_mar_2026.csv" http://127.0.0.1:8001/readings/upload'),
            callout("info", "<strong>The data survives a restart.</strong> It's in <code>readings.db</code>, in <code>code/</code>. Stop uvicorn, "
                            "start it again, and <code>GET /readings/stats</code> still says 5,664."),
        ])),
        dict(title="Part 2 · Step 5 — Test every endpoint", steps=["Run", "Observe"], body="".join([
            code(f"{CODE}/5_test_readings.py"),
            "<p>With the readings API running (first terminal), run the test in a <b>second terminal</b>. It empties the database first and ends with the "
            "5,664 readings loaded again:</p>",
            cmd("cd code\npython 5_test_readings.py"),
            output(read_test),
            table(["Status", "Here, when"], [
                ["<b>201</b> Created", "An upload was accepted — the report lists any rows refused"],
                ["<b>400</b> Bad request", "Not a .csv, wrong columns, or more than 7 days asked for"],
                ["<b>404</b> Not found", "No readings for that day"],
                ["<b>422</b> Unprocessable", "The request broke the endpoint's rules (<code>top=0</code>, a date that isn't a date)"]]),
        ])),
        dict(title="Part 3 · Step 1 — What we add to make it MCP: 6_mcp_server.py", steps=["Concept", "What we add", "Code", "Run"], body="".join([
            learn(["MCP (Model Context Protocol): how an AI app asks a server <em>\"what can you do, and what do you need?\"</em>",
                   "What we add to REST to make it MCP: one library, one file, one decorator per function",
                   "Not every endpoint becomes a tool: an AI reads; changing data stays with a person"]),
            "<p>Our two APIs are for <strong>people and programs</strong>: someone reads <code>/docs</code> and knows which URL to call. An <strong>AI app</strong> "
            "(Cursor, Claude, VS Code Copilot) needs to <em>ask the server</em> what it can do — and get names, descriptions and argument rules it can use. "
            "That is MCP. We add <b>one file</b>; <code>calculator.py</code>, <code>readings.py</code> and <code>db.py</code> don't change.</p>",
            flow([("calculator.py", "+ readings.py", True), ("1_ · 3_ …_api.py", "REST: /docs", False), ("6_mcp_server.py", "MCP: 5 tools", True),
                  ("Browser · Cursor", "two kinds of client", False)], "<b>One logic, two doors.</b> Both import the same functions — nothing is copied."),
            table(["", "REST (<code>1_</code>, <code>3_</code>)", "MCP (<code>6_mcp_server.py</code>)"], [
                ["Library", "<code>fastapi</code>, <code>uvicorn</code>", "<code>mcp</code> (in <code>requirements.txt</code>)"],
                ["The server object", "<code>app = FastAPI(...)</code>", "<code>mcp = MCPServer(\"campus-energy-v2\", ...)</code>"],
                ["Publish a function", "<code>@app.get(\"/summary\")</code>: a method <em>and</em> a URL", "<code>@mcp.tool()</code>: just a name, <code>day_summary</code>"],
                ["Inputs and limits", "Type hints, <code>Query(...)</code>, <code>Literal</code>", "<strong>The same</strong> type hints, with <code>Field(description=...)</code>"],
                ["What a client reads", "<code>/docs</code>, for a person", "<code>tools/list</code>: name, docstring, JSON Schema — for an AI app"],
                ["The docstring", "Optional", "<strong>Essential</strong>: it is all the AI knows about the tool"],
                ["Saying \"no\"", "<code>HTTPException(400 / 404)</code>", "<code>ToolError(...)</code> → <code>isError: true</code> and the reason"],
                ["Port", "8000 and 8001", "8002, at <code>/mcp</code>"]]),
            "<p><strong>Each read endpoint becomes a tool with a name</strong> — and the two that change data don't:</p>",
            table(["REST endpoint", "MCP tool", "Same function"], [
                ["<code>GET /calculate</code>, <code>POST /calculate</code>", "<code>calculate</code>", "<code>calculator.calculate</code>"],
                ["<code>GET /readings/stats</code>", "<code>readings_stats</code>", "<code>readings.stats</code>"],
                ["<code>GET /readings</code>", "<code>get_readings</code>", "<code>readings.get_readings</code>"],
                ["<code>GET /summary</code>", "<code>day_summary</code>", "<code>readings.summary</code>"],
                ["<code>GET /peak-days</code>", "<code>peak_days</code>", "<code>readings.peak_days</code>"],
                ["<code>POST /readings/upload</code>, <code>DELETE /readings</code>", "— (REST only)", "They change data: a person does that, not an AI"]]),
            code(f"{CODE}/6_mcp_server.py"),
            cmd("cd code\npython 6_mcp_server.py http          # → http://127.0.0.1:8002/mcp   (another port: python 6_mcp_server.py http 8012)"),
            callout("warn", "<strong>Say \"no\" with <code>ToolError</code>.</strong> If a tool lets an ordinary error escape, the AI app sees only "
                            "<em>\"Error executing tool day_summary\"</em>, without the reason. <code>refused_as_tool_error()</code> passes on "
                            "<em>\"no readings for 2026-05-01\"</em> instead. Status codes (400, 404) are a REST idea; MCP says <code>isError</code> and why."),
            callout("info", "<strong>Load the data first.</strong> The MCP tools read the same <code>readings.db</code> that <code>POST /readings/upload</code> "
                            "fills (Part 2). No upload, no readings — and <code>readings_stats</code> says 0."),
        ])),
        dict(title="Part 3 · Step 2 — The two lists: REST endpoints and MCP tools", steps=["Run", "Compare"], body="".join([
            code(f"{CODE}/7_list_api_and_tools.py"),
            cmd("cd code\npython 7_list_api_and_tools.py"),
            output(lists),
            callout("tip", "REST has <b>9</b> endpoints across two APIs; MCP has <b>5</b> tools. Same functions — but only the ones an AI should use."),
        ])),
        dict(title="Part 3 · Step 3 — Test every tool, as an AI app would", steps=["Run", "Observe"], body="".join([
            "<p>With the MCP server running (<code>python 6_mcp_server.py http</code>) — and, to compare, the readings API too — run in a "
            "<b>second terminal</b>:</p>",
            code(f"{CODE}/8_test_mcp.py"),
            cmd("cd code\npython 8_test_mcp.py"),
            output(mcp_test),
            table(["REST says", "MCP says"], [
                ["<b>200</b> and JSON", "<code>isError: false</code> and the result"],
                ["<b>400</b> / <b>404</b> — our function refused", "<code>isError: true</code> and the reason (<code>ToolError</code>)"],
                ["<b>422</b> — the request broke the rules", "<code>isError: true</code> — the schema refused it, our code never ran"]]),
        ])),
        dict(title="Part 3 · Step 4 — MCP on the wire: four messages", steps=["Concept", "Run"], body="".join([
            "<p><code>Client(...)</code> hides the protocol. Underneath, every MCP client — Cursor, MCP Inspector, <code>8_test_mcp.py</code> — sends "
            "the same four <b>JSON-RPC</b> messages, each an HTTP POST to <code>/mcp</code>:</p>",
            table(["#", "<code>method</code>", "What it does", "What comes back"], [
                ["①", "<code>initialize</code>", "Agree the protocol version", "The server's name and abilities, and an <code>mcp-session-id</code> <em>response header</em>, sent back on every later message"],
                ["②", "<code>notifications/initialized</code>", "\"I'm ready.\" No <code>id</code>: a notification", "HTTP 202, empty"],
                ["③", "<code>tools/list</code>", "\"What tools do you have?\"", "Each tool's name, description and JSON Schema — from the type hints"],
                ["④", "<code>tools/call</code>", "Run one tool with its arguments", "The result, with <code>isError</code>"]]),
            code(f"{CODE}/9_mcp_on_the_wire.py"),
            cmd("cd code\npython 9_mcp_on_the_wire.py"),
            output(wire),
            callout("tip", "<strong>stdio or HTTP?</strong> Over HTTP (<code>python 6_mcp_server.py http</code>) you start the server and give the app its URL. "
                           "Over stdio (<code>python 6_mcp_server.py stdio</code>) the AI app starts the server itself and talks through stdin/stdout — no port, "
                           "no session header: the process is the session."),
        ])),
        dict(title="Part 3 · Step 5 — Connect Cursor, and see all five tools", steps=["Start", "Connect", "Use"], body="".join([
            try_it(["Load the data if you haven't (Part 2): <code>python 3_readings_api.py</code>, then <code>python 4_upload_csv.py</code>",
                    "Start the MCP server and leave it running: <code>python 6_mcp_server.py http</code>",
                    "Copy <code>cursor_mcp.json</code> to <code>.cursor/mcp.json</code> in the folder you opened in Cursor (or <code>~/.cursor/mcp.json</code> for every project)",
                    "Open Cursor's settings → <b>Tools &amp; MCP</b> (newer versions: <b>Customize</b> in the sidebar): <code>campus-energy-v2</code> shows a green dot. "
                    "Switch it on — it lists the <b>5 tools</b>",
                    "In the chat (<b>Agent</b> mode) ask <em>\"Was the transformer overloaded on 23 March 2026?\"</em> — Cursor proposes <code>day_summary</code> with "
                    "<code>day: \"2026-03-23\"</code>; approve it → <b>106.4 %, OVERLOAD</b>",
                    "Ask <em>\"What is 12 divided by 3?\"</em> → <code>calculate</code>. Then <em>\"Which 3 days were worst?\"</em> → <code>peak_days</code>",
                    "Ask <em>\"Delete all the readings\"</em> — there is no such tool, so Cursor can't. That is on purpose"]),
            code(f"{CODE}/cursor_mcp.json", "json"),
            callout("tip", "<strong>Not working?</strong> A red dot or no tools: the server isn't running, or the URL isn't exactly <code>/mcp</code> on port 8002. "
                           "Changed the code? Restart the server, then switch it off and on in Cursor. Cursor's side: Output panel (<code>Cmd+Shift+U</code>) → "
                           "<b>MCP Logs</b>. No terminal at all: <code>cursor_mcp_stdio.json</code> makes Cursor start <code>6_mcp_server.py</code> itself (full paths)."),
            "<p><strong>REST and MCP: the difference in the UI.</strong></p>",
            table(["", "REST — /docs (Swagger)", "MCP — Cursor / MCP Inspector"], [
                ["The list", "Endpoints by URL and method", "Tool names and descriptions"],
                ["How you call it", "<b>You</b> pick the endpoint, fill the boxes, press <i>Execute</i>", "<b>You type a sentence</b>; the model picks the tool and fills the arguments; you approve"],
                ["What comes back", "A status code and JSON", "A result with <code>isError</code>; the model puts it in words"],
                ["Try it without an AI", "<code>/docs</code>", "MCP Inspector: <code>npx -y @modelcontextprotocol/inspector</code> → <code>http://127.0.0.1:8002/mcp</code>"]]),
            "<p><strong>Claude Code</strong> connects to the same server. One command in <code>code/</code> writes <code>.mcp.json</code> — already in the "
            "folder, so everyone who opens it gets the server:</p>",
            cmd("claude mcp add --transport http --scope project campus-energy-v2 http://127.0.0.1:8002/mcp\nclaude mcp list          # campus-energy-v2 … Pending approval\nclaude                   # approve it once when asked, then ask: \"Was the transformer overloaded on 23 March 2026?\""),
            code(f"{CODE}/.mcp.json", "json"),
            callout("info", "<strong>Why \"Pending approval\"?</strong> A project's <code>.mcp.json</code> could point anywhere, so Claude Code asks you once before it "
                            "connects. Approve it in <code>claude</code> (or <code>/mcp</code> inside it). The screens are in the last step."),
        ])),
        dict(title="Part 3 · Step 6 — A UI for the tools: 10_mcp_ui.py", steps=["Concept", "Code", "Run", "Try"], body="".join([
            learn(["A Streamlit page that is an MCP <em>client</em>: it lists the tools (<code>tools/list</code>) and calls one (<code>tools/call</code>)",
                   "Forms built from each tool's JSON Schema — the page knows nothing about our tools in advance",
                   "The difference from Cursor: here <b>you</b> pick the tool and fill it; in Cursor the model does"]),
            "<p>Cursor and Claude Code show the tools to a model. This page shows them to <b>you</b>: every tool the server offers, its inputs and description, "
            "and a form to call it. Each field comes from the schema — <code>enum</code> becomes a drop-down, <code>integer</code> with "
            "<code>minimum</code>/<code>maximum</code> a number box with limits, <code>format: date</code> a date picker. Point it at any MCP server "
            "and it works the same.</p>",
            code(f"{CODE}/10_mcp_ui.py"),
            cmd("cd code\npython 6_mcp_server.py http          # terminal 1 — the MCP server\nstreamlit run 10_mcp_ui.py            # terminal 2 → http://localhost:8501"),
            image("v2_ui_tools.png", "The list of 5 tools from <code>tools/list</code>; <b>day_summary</b> chosen, its date filled, called → the JSON-RPC message sent, "
                                     "<code>isError: false</code>, and 23 March's numbers (106.4 %)."),
            try_it(["Call <b>calculate</b> with a = 12, b = 3, op = div → 4.0. Then b = 0 → <code>isError: true</code> — <em>cannot divide by zero</em>",
                    "Call <b>day_summary</b> for 2026-05-01 → <em>no readings for 2026-05-01</em>",
                    "Call <b>get_readings</b> for 12:00 → 13:00 on 23 March (4 rows); then set <code>end</code> to April → refused: <em>at most 7 days</em>",
                    "Open <b>Its JSON Schema</b> under a form — that is exactly what Cursor's model reads to choose and fill the tool",
                    "Stop the MCP server and press <b>Connect / refresh</b> — one clear line: <em>Nothing is running at …</em>"]),
        ])),
        dict(title="Check yourself", kind="quiz", body=quiz([
            {"q": "GET /calculate?a=2&b=3&op=pow returns…", "options": ["200", "400", "422", "404"], "answer": 2,
             "why": "op may only be add, sub, mul or div — FastAPI refuses it before our function runs."},
            {"q": "GET /calculate?a=1&b=0&op=div returns 400. Who refused it?", "options": ["FastAPI", "Our calculate() function, with a ValueError", "The browser", "SQLite"], "answer": 1,
             "why": "The request followed the rules; the maths can't be done, so our function said no and the API turned it into 400."},
            {"q": "Why is calculator.py separate from 1_calculator_api.py?", "options": ["Python needs two files", "So other doors (tests, MCP) can use the same logic without the web code", "For speed", "FastAPI requires it"], "answer": 1,
             "why": "In Part 3 the MCP server imports calculator.py — nothing is copied."},
            {"q": "You upload a file where 6 of 9 rows have mistakes. What happens?", "options": ["Nothing is loaded", "The 3 good rows are loaded; the report lists the 6 refused rows and why", "All 9 are loaded", "The server crashes"], "answer": 1,
             "why": "Every row is checked; good rows are stored and each refusal is reported by line."},
            {"q": "GET /summary?day=2026-05-01 returns 404. Why?", "options": ["The URL is wrong", "There are no readings for that day — the data is 1 Feb – 31 Mar", "The server is down", "May isn't allowed"], "answer": 1,
             "why": "404 means the request was fine but the data isn't there."},
            {"q": "What do we ADD to make the REST logic available to Cursor?", "options": ["Rewrite calculator.py", "One file (6_mcp_server.py) and the mcp library", "A new database", "Nothing — Cursor reads /docs"], "answer": 1,
             "why": "The MCP server imports the same calculator.py and readings.py; each function gets @mcp.tool()."},
            {"q": "8_test_mcp.py asks day_summary for 2026-05-01. What comes back?", "options": ["404", "isError: true and \"no readings for 2026-05-01\"", "An empty answer", "The server crashes"], "answer": 1,
             "why": "MCP has no status codes: a ToolError carries the reason to the AI app."},
            {"q": "Which endpoints should NOT become MCP tools for an AI?", "options": ["/summary", "/peak-days", "Upload and delete — they change data", "/readings/stats"], "answer": 2,
             "why": "Give an AI only what it needs; changing or deleting data stays with a person."}])),
        dict(title="Testing screens — every part, run for real", steps=["Part 1", "Part 2", "Part 3", "Claude Code", "Cursor"], body="".join([
            "<p>What you should see at each step. Every screen is a real run on the workshop laptop — the APIs on 8000 and 8001, the MCP server on 8002.</p>",
            "<h3>Part 1 · Calculator API (port 8000)</h3>",
            image("v2_calc_docs.png", "<code>http://127.0.0.1:8000/docs</code> — FastAPI wrote this page from <code>1_calculator_api.py</code>: one GET and one POST for <code>/calculate</code>."),
            image("v2_calc_try.png", "<b>GET /calculate</b> → Try it out → a = 12, b = 3, op = div → Execute → <b>200</b>, <code>\"result\": 4</code>. The curl line shows the same request for a terminal."),
            image("v2_term_2_test_calculator.png", "<code>python 2_test_calculator.py</code> in a second terminal: 200 for answers, 400 when our function refuses (÷ 0), 422 when FastAPI refuses the request."),
            "<h3>Part 2 · Readings API (port 8001)</h3>",
            image("v2_read_docs.png", "<code>http://127.0.0.1:8001/docs</code> — six endpoints: upload, delete, and four that answer questions."),
            image("v2_read_upload_problems.png", "<b>POST /readings/upload</b> with <code>readings_with_problems.csv</code>: <b>201</b> — 3 loaded, 6 refused, each with its line and reason."),
            image("v2_read_upload.png", "The same endpoint with <code>campus_feb_mar_2026.csv</code>: all <b>5,664</b> readings loaded, 1 Feb → 31 Mar."),
            image("v2_read_summary.png", "<b>GET /summary</b> with <code>2026-03-23</code>: peak loading <b>106.4 %</b> at 12:45 — <b>OVERLOAD</b>."),
            image("v2_term_4_upload_csv.png", "<code>python 4_upload_csv.py</code> — the same upload from a program: it first checks it found the Readings API."),
            image("v2_term_5_test_readings.png", "<code>python 5_test_readings.py</code> — every endpoint, including the refusals (404, 400, 422). It ends with the data loaded again."),
            "<h3>Part 3 · MCP server (port 8002)</h3>",
            image("v2_term_6_mcp_server.png", "Terminal 1: <code>python 6_mcp_server.py http</code> — leave it running."),
            image("v2_term_7_list.png", "<code>python 7_list_api_and_tools.py</code> — 9 REST endpoints, 5 MCP tools, and which matches which."),
            image("v2_term_8_test_mcp.png", "<code>python 8_test_mcp.py</code> — every tool as an AI app calls it; refusals come back as <code>isError=True</code> with the reason; REST and MCP give the same answer."),
            image("v2_ui_tools.png", "<code>streamlit run 10_mcp_ui.py</code> — the tools from <code>tools/list</code>, and <b>day_summary</b> called from its form: 106.4 %."),
            image("v2_ui_refusal.png", "The same UI, <b>get_readings</b> for more than 7 days: <code>isError: true</code> and the server's reason; the calls so far below."),
            image("v2_term_9_wire.png", "<code>python 9_mcp_on_the_wire.py</code> — the four JSON-RPC messages, the session id in the response header, and the 400 without it."),
            "<h3>Claude Code</h3>",
            image("v2_term_claude_code.png", "<code>claude mcp add … --scope project</code> writes <code>.mcp.json</code>; <code>claude mcp get</code> shows it waiting for your one-time approval."),
            image("v2_term_claude_code_tools.png", "Once loaded, Claude Code reports <code>campus-energy-v2</code> <b>connected</b> with the 5 tools, named <code>mcp__campus-energy-v2__…</code>."),
            callout("tip", "<strong>Your turn:</strong> run <code>claude</code> in <code>code/</code>, approve <code>campus-energy-v2</code>, and ask <em>\"Was the transformer overloaded "
                           "on 23 March 2026?\"</em> — Claude Code asks to run <code>day_summary</code>; allow it and it answers 106.4 %, OVERLOAD. "
                           "Screenshot that for your report."),
            "<h3>Cursor</h3>",
            "<p><code>.cursor/mcp.json</code> is already in <code>code/</code>. Open the <code>code/</code> folder in Cursor with the MCP server running, then capture:</p>",
            try_it(["<b>Settings → Tools &amp; MCP</b> (or <b>Customize</b>): <code>campus-energy-v2</code> with a green dot and its <b>5 tools</b>",
                    "<b>Agent</b> chat: <em>\"Was the transformer overloaded on 23 March 2026?\"</em> — the <code>day_summary</code> call card (click the arrow to show "
                    "<code>day: \"2026-03-23\"</code>) and the answer, 106.4 %, OVERLOAD",
                    "<em>\"Delete all the readings\"</em> — Cursor has no tool for it and says so"]),
        ])),
        dict(title="MCP Inspector — the Swagger of MCP", steps=["Concept", "Start", "Connect", "Tools", "Run"], body="".join([
            learn(["Where an MCP server's “documentation” comes from: the <code>tools/list</code> reply — name, description, JSON Schema",
                   "MCP Inspector, the official tool for looking inside any MCP server — what Swagger (<code>/docs</code>) is for REST",
                   "Run a tool by hand, read its answer or its refusal, and watch every JSON-RPC message"]),
            "<p>A REST API built with FastAPI gives you <code>/docs</code> for free. An MCP server has no page of its own — it only answers messages. "
            "But it describes itself: <code>tools/list</code> returns every tool's <b>name</b>, its <b>description</b> (the docstring) and the "
            "<b>JSON Schema</b> of its inputs (from the type hints and <code>Field(description=…)</code>). Any MCP client can turn that into a page. "
            "<b>MCP Inspector</b>, from the people who make MCP, is the standard one.</p>",
            table(["", "REST (FastAPI)", "MCP"], [
                ["The page", "<code>/docs</code> (Swagger), built in", "MCP Inspector — a separate tool you start"],
                ["Machine-readable spec", "<code>/openapi.json</code>", "the <code>tools/list</code> reply"],
                ["The explanation", "the docstring, <code>Query(description=…)</code>", "the docstring, <code>Field(description=…)</code>"],
                ["Try it", "Try it out → Execute", "pick a tool → fill the form → Execute Tool"],
                ["A refusal", "400 / 404 with <code>detail</code>", "<b>Tool Error</b> with the reason (<code>isError: true</code>)"]]),
            "<h3>1 · Start it</h3>",
            "<p>Keep the MCP server running in terminal 1. In terminal 2 (needs Node.js — the first run downloads the Inspector):</p>",
            cmd("cd code\npython 6_mcp_server.py               # terminal 1 — leave it running (port 8002)\nnpx @modelcontextprotocol/inspector   # terminal 2 — opens http://127.0.0.1:6274"),
            image("v2_term_inspector.png", "The Inspector starts on <b>6274</b>. Open the address it prints — the token in it is new every time and keeps other web pages out."),
            "<h3>2 · Add our server and connect</h3>",
            "<p><b>Add Servers → + Add manually</b>. Server ID <code>campus-energy-v2</code>, Transport <b>streamable-http</b>, URL "
            "<code>http://127.0.0.1:8002/mcp</code> → <b>Add</b>. Then switch it on.</p>",
            image("v2_insp_add.png", "The <b>Add server</b> form: a name, the transport (<b>streamable-http</b> — the same as <code>transport=\"streamable-http\"</code> in "
                                     "<code>6_mcp_server.py</code>), and the URL."),
            image("v2_insp_connected.png", "<b>Connected</b>, speaking MCP 2025-11-25. On the right, the Inspector has already sent <code>tools/list</code>, "
                                           "<code>prompts/list</code> and <code>resources/templates/list</code>."),
            "<h3>3 · The tools — what each does and what it takes</h3>",
            image("v2_insp_tools.png", "<b>Tools</b> tab: the 5 tools from <code>tools/list</code>. Open <b>day_summary</b>: its description is our docstring; "
                                       "<b>Day *</b> (required) with <em>the day, YYYY-MM-DD, e.g. 2026-03-23</em> is our <code>Field(description=…)</code>. "
                                       "<b>Edit as JSON</b> shows the raw arguments."),
            "<h3>4 · Run it — an answer and a refusal</h3>",
            image("v2_insp_result.png", "<b>Execute Tool</b> → the result: 23 March, peak loading <b>106.4 %</b>, <b>OVERLOAD</b>. The call appears in "
                                        "<b>Messages</b> as <code>tools/call · day_summary</code>."),
            image("v2_insp_refusal.png", "<b>calculate</b> with a = 12, b = 0, op = div → <b>Tool Error</b>: <em>cannot divide by zero</em> — the "
                                         "<code>ToolError</code> from <code>6_mcp_server.py</code>, exactly what an AI app receives."),
            try_it(["Open each of the 5 tools and read its description and inputs. Which tool takes no input at all?",
                    "<b>peak_days</b>: try <code>top</code> = 40 — the schema says 1–31, so it is refused before our function runs",
                    "<b>get_readings</b> from 2026-03-01T00:00 to 2026-03-31T00:00 → <em>at most 7 days</em>",
                    "Click a <code>tools/call</code> in <b>Messages</b> to see the exact JSON-RPC request and response",
                    "Change a docstring in <code>6_mcp_server.py</code>, restart it, reconnect — the Inspector shows the new text. That is all the AI reads"]),
            callout("tip", "<strong>Inspector, 10_mcp_ui.py, Cursor — the same two messages.</strong> All three send <code>tools/list</code> and "
                           "<code>tools/call</code>. The Inspector and our Streamlit page let <b>you</b> choose the tool; Cursor lets the model choose. "
                           "Not connecting? The MCP server must be running with HTTP (<code>python 6_mcp_server.py</code>) and the URL must end in <code>/mcp</code>."),
        ])),
    ]


# ── the page ───────────────────────────────────────────────────────────────────────────────────────
HEAD = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>REST to MCP · MGIT Workshop v2</title>
  <meta name="description" content="Build a calculator API and a readings API with FastAPI, then open the same logic to AI apps with MCP.">
  <link rel="icon" type="image/png" href="assets/img/favicon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&family=Montserrat:wght@700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/actoryx.css">
  <link rel="stylesheet" href="assets/css/workshop.css">
</head>
<body data-chapter="v2-rest-mcp">
<!-- Generated by tools/build_page.py — edit that file, not this one. -->
<header class="topbar">
  <div class="wrap">
    <a class="brand" href="index.html" aria-label="Workshop home">
      <img class="logo-light" src="assets/img/actoryx-wordmark-compact.png" alt="Actoryx">
      <img class="logo-dark" src="assets/img/actoryx-wordmark-compact-dark.png" alt="Actoryx">
      <span class="divider" aria-hidden="true"></span>
      <span class="partner">MGIT · Workshop v2</span>
    </a>
    <span class="spacer"></span>
    <button class="btn-ghost sidebar-toggle" type="button">☰ Steps</button>
    <button class="btn-ghost" type="button" data-theme-toggle aria-label="Toggle dark mode">◐</button>
  </div>
</header>
"""


def page(secs):
    out = [HEAD, """<main class="wrap">
  <section class="chapter-head">
    <span class="eyebrow">Workshop v2 · REST first, then MCP</span>
    <h1>From a REST API to MCP tools</h1>
    <p class="muted">Part 1: a calculator API. Part 2: an API that loads 5,664 substation readings from an uploaded CSV and answers questions about them.
    Part 3: the same logic as MCP tools, connected to Cursor.</p>
    <div class="meta"><span class="tag">FastAPI</span><span class="tag">SQLite</span><span class="tag">File upload</span>
    <a class="tag" href="downloads/v2_workshop.zip" download>📦 Download everything (.zip)</a>
    <a class="tag" href="slides/V2_REST_to_MCP.pptx" download>📊 Slides (.pptx)</a></div>
  </section>
  <div class="layout">
    <aside class="sidebar card" aria-label="Steps"><div class="label">v2 · Steps</div><ol id="lesson-list"></ol></aside>
    <div>"""]
    for i, sec in enumerate(secs, 1):
        kind = sec.get("kind", "")
        k = f' data-kind="{kind}"' if kind else ""
        icon = "📝 " if kind == "quiz" else ""
        out.append(f'<section class="lesson card" data-title="{esc(sec["title"])}"{k}>\n<h2>{i}. {icon}{sec["title"]}</h2>')
        if sec.get("steps"):
            out.append('<div class="steps">' + "".join(f"<span>{s}</span>" for s in sec["steps"]) + "</div>")
        out.append(sec["body"])
        out.append("</section>")
    out.append("""    </div>
  </div>
</main>
<div class="bottombar"><div class="wrap"><span class="title">v2 — From a REST API to MCP tools</span>
<button class="btn primary" type="button" id="mark-complete">Mark complete ✓</button></div></div>
<script src="assets/js/course.js"></script>
</body>
</html>""")
    return "\n".join(out)


def make_zip():
    out = V2 / "downloads" / "v2_workshop.zip"
    out.parent.mkdir(exist_ok=True)
    files = [f for f in sorted((V2 / CODE).rglob("*"))
             if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".db" and f.name != ".DS_Store"]
    files += [V2 / "requirements.txt", V2 / "README.md"]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, Path("mgit_v2") / f.relative_to(V2))
    print(f"✓ downloads/v2_workshop.zip — {len(files)} files, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    secs = sections()
    (V2 / "index.html").write_text(page(secs))
    print(f"✓ index.html — {len(secs)} sections")
    make_zip()
