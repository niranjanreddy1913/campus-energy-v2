# MGIT workshop v2: from a REST API to MCP tools

**Student page:** [`index.html`](index.html). Every code box on it is read from the files in `code/`, and every output comes from running them.

**Slides:** [`slides/V2_REST_to_MCP.pptx`](slides/V2_REST_to_MCP.pptx) has 24 slides in the Actoryx format, with trainer notes. It follows the page part by part and uses the same real screenshots. It's built by `node tools/build_deck.js`, which reads the code snippets from `code/`.

We build two small REST APIs first, then open the **same** logic to AI apps (Cursor, Claude, VS Code) with MCP. The one rule throughout: **the logic lives in plain Python functions** (`calculator.py`, `readings.py`) with no web code. `app.py` only receives a request, calls a function and returns its answer. That is what makes Part 3 a matter of adding one file.

**Everything is in one folder, `code/`.** The numbers are the order you run things in. `calculator.py`, `readings.py` and `db.py` have no number because the APIs *import* them, and Python can't `import` a name that starts with a digit. (`uvicorn` and `importlib` can. That's how the numbered files are run and tested. Each API also starts with `python 1_calculator_api.py` or `python 3_readings_api.py`, from any folder.)

| Part | What we build | The new idea |
|---|---|---|
| **1 · Calculator API** | Two numbers and one operation in, the answer out | GET and POST, query vs JSON body, `/docs`, status codes 200 / 400 / 422 |
| **2 · Readings API** | Upload a CSV of 5,664 substation readings **through the API**, then ask questions about them | File upload, checking every row, a database (SQLite), query endpoints, 404 |
| **3 · MCP** | The same two APIs as MCP tools, connected to Cursor | Tools an AI app discovers and calls; REST and MCP side by side |

## Set up once

From this folder:

```bash
pip install -r requirements.txt
```

Then work in `code/` for everything:

```bash
cd code
```

## Ports

| API | Port | Start it | Its programs use |
|---|---|---|---|
| Calculator (Part 1) | **8000** | `python 1_calculator_api.py` | `2_test_calculator.py` |
| Readings (Part 2) | **8001** | `python 3_readings_api.py` | `4_upload_csv.py`, `5_test_readings.py` |
| MCP server (Part 3) | **8002**, at `/mcp` | `python 6_mcp_server.py http` | `8_test_mcp.py`, `9_mcp_on_the_wire.py`, Cursor |

Both can run at the same time. To use another port, run `python 1_calculator_api.py 8010` and then `API_URL=http://127.0.0.1:8010 python 2_test_calculator.py`. The same works for 8001.

## The files, in order

| File | Part | What it is | How you use it |
|---|---|---|---|
| `calculator.py` | 1 | The logic: `calculate(a, b, op)` for add, sub, mul, div. Refuses ÷ 0 with a `ValueError` | `python calculator.py` runs a quick check |
| `1_calculator_api.py` | 1 | The calculator REST API, on **port 8000** | `python 1_calculator_api.py` (or `uvicorn 1_calculator_api:app --reload`), then open http://127.0.0.1:8000/docs |
| `2_test_calculator.py` | 1 | Every case, with the replies, from the **running** API on port 8000 | `python 2_test_calculator.py` (second terminal) |
| `db.py` | 2 | The database: `readings.db` (SQLite) in this folder, with one table, `readings` | — |
| `readings.py` | 2 | The logic: `load_csv` checks and loads a file; `stats`, `get_readings`, `summary` and `peak_days` answer questions | — |
| `3_readings_api.py` | 2 | The readings REST API: 6 endpoints, on **port 8001** | `python 3_readings_api.py` (or `uvicorn 3_readings_api:app --reload --port 8001`), then open http://127.0.0.1:8001/docs |
| `4_upload_csv.py` | 2 | Uploads the CSV to the **running** API | `python 4_upload_csv.py` (second terminal) |
| `5_test_readings.py` | 2 | Every endpoint of the **running** API on port 8001, including the refusals. It empties the database first and ends with the 5,664 readings loaded again | `python 5_test_readings.py` (second terminal) |
| `6_mcp_server.py` | 3 | The **same** logic as 5 MCP tools for AI apps. Imports `calculator.py` and `readings.py`; nothing is copied | `python 6_mcp_server.py` or `python 6_mcp_server.py http` (port 8002; also PyCharm's Run button), or `python 6_mcp_server.py stdio` (started by the AI app) |
| `7_list_api_and_tools.py` | 3 | The REST endpoints of both APIs and the MCP tools, side by side, read from the code | `python 7_list_api_and_tools.py` (no server needed) |
| `8_test_mcp.py` | 3 | Calls every tool of the **running** MCP server, as Cursor would. If the readings API is running too, it checks REST and MCP give the same answer | `python 8_test_mcp.py` (second terminal) |
| `9_mcp_on_the_wire.py` | 3 | The four JSON-RPC messages an MCP client sends, typed by hand | `python 9_mcp_on_the_wire.py` (MCP server running) |
| `10_mcp_ui.py` | 3 | A **Streamlit UI** for any MCP server: lists the tools (`tools/list`) and calls one from a form built from its JSON Schema (`tools/call`) | `streamlit run 10_mcp_ui.py` (MCP server running) → http://localhost:8501 |
| `cursor_mcp.json`, `cursor_mcp_stdio.json` | 3 | Connect Cursor over HTTP (port 8002), or let Cursor start the server itself (stdio) | Copy one to `.cursor/mcp.json` |
| `.cursor/mcp.json` | 3 | Already in place: open `code/` in Cursor and it finds `campus-energy-v2` | — |
| `.mcp.json` | 3 | The same server for **Claude Code**, written by `claude mcp add --scope project` | `claude` in `code/`, then approve it once |
| `campus_feb_mar_2026.csv` | 2 | 5,664 readings, one every 15 minutes, 1 Feb – 31 Mar 2026: `timestamp`, `load_kw`, `solar_kw`, `ambient_c`, `irradiance_wm2` | Upload it through the API |
| `readings_with_problems.csv` | 2 | 9 rows with deliberate mistakes (3 are good) | Upload it to see the checks |

## Part 1 · Calculator API

| Endpoint | Inputs | Example | Reply |
|---|---|---|---|
| `GET /` | — | — | A welcome message |
| `GET /calculate` | `a`, `b`, `op` in the address | `/calculate?a=12&b=3&op=div` | **200** `{"result": 4.0}` |
| `POST /calculate` | JSON body `{"a", "b", "op"}` | `{"a": 12, "b": 3, "op": "div"}` | **200** `{"result": 4.0}` |

When the API says no:
- **400** when our function refuses the values. `1 ÷ 0` gives *"cannot divide by zero"*.
- **422** when the request breaks the endpoint's rules, which FastAPI checks before our code runs. Examples: `op=pow`, `a=twelve`, or `b` missing.

## Part 2 · Readings API

| Method | Endpoint | Inputs | What it does |
|---|---|---|---|
| POST | `/readings/upload` | A CSV file, and `replace` (true / false) | Loads the file, checking every row. Returns a report: rows loaded, rows refused and why, what's in the database |
| GET | `/readings/stats` | — | How many readings are loaded, from when to when |
| GET | `/readings` | `start`, `end` | The raw 15-minute rows, at most 7 days at a time |
| GET | `/summary` | `day` | One day: peak load, energy, solar, peak loading % and status (NORMAL / HIGH / OVERLOAD) |
| GET | `/peak-days` | `top` (1–31) | The days the transformer worked hardest |
| DELETE | `/readings` | — | Removes everything, to start again |

**The order to run things** (in `code/`):
1. `python 3_readings_api.py`. Leave it running. It uses **port 8001**, so it can run next to the calculator API on 8000. `4_upload_csv.py` and `5_test_readings.py` use 8001 too, and check that they found the Readings API before sending anything.
2. Load the data, in any one of three ways:
   - **In http://127.0.0.1:8001/docs:** POST /readings/upload → **Try it out** → **Choose file** → `campus_feb_mar_2026.csv` → **Execute**.
   - **From a program:** `python 4_upload_csv.py`, in a second terminal.
   - **With curl:** `curl -F "file=@campus_feb_mar_2026.csv" http://127.0.0.1:8001/readings/upload`
3. Ask: `GET /summary?day=2026-03-23` returns **106.4 %, OVERLOAD** at 12:45. `GET /peak-days?top=3` returns **24 Feb 112.8 %, 17 Mar 109.8 %, 18 Mar 108.6 %**.

**The upload checks every row.** `readings_with_problems.csv` (9 rows) loads 3 and refuses 6, each with its line number and reason:
- a word where a number should be;
- 30 February;
- negative solar;
- 80 °C air;
- a duplicate time;
- an empty load.

A wrong file is refused as a whole (400): `.txt` instead of `.csv`, or missing columns. Uploading the same file again with `replace=false` adds nothing; it reports "already there 5,664". The data survives a restart, because it's in `readings.db`.

**Transformer loading** = (load − solar) ÷ 0.93 ÷ 630 kVA. Rooftop solar supplies part of the load, so transformer TR-MAIN carries only the rest. Above 80 % it's HIGH, and above 100 % it's OVERLOAD.

## Part 3 · MCP: the same logic for AI apps

**What we add:** one file, `6_mcp_server.py`, and one library, `mcp`. `calculator.py`, `readings.py` and `db.py` don't change.

| | REST (`1_`, `3_`) | MCP (`6_mcp_server.py`) |
|---|---|---|
| Library | `fastapi`, `uvicorn` | `mcp` |
| The server object | `app = FastAPI(...)` | `mcp = MCPServer("campus-energy-v2", ...)` |
| Publish a function | `@app.get("/summary")`: a method **and** a URL | `@mcp.tool()`: just a name, `day_summary` |
| Inputs and limits | Type hints, `Query(...)`, `Literal` | **The same** type hints, with `Field(description=...)` |
| What a client reads | `/docs`, for a person | `tools/list`: name, docstring, JSON Schema, for an AI app |
| The docstring | Optional | **Essential**: it's all the AI knows about the tool |
| Saying "no" | `HTTPException(400 / 404)` | `ToolError(...)` gives `isError: true` and the reason |
| Port | 8000, 8001 | 8002, at `/mcp` |

| REST endpoint | MCP tool | Same function |
|---|---|---|
| `GET` / `POST /calculate` | `calculate` | `calculator.calculate` |
| `GET /readings/stats` | `readings_stats` | `readings.stats` |
| `GET /readings` | `get_readings` | `readings.get_readings` |
| `GET /summary` | `day_summary` | `readings.summary` |
| `GET /peak-days` | `peak_days` | `readings.peak_days` |
| `POST /readings/upload`, `DELETE /readings` | **none, REST only** | These change data. A person does that, not an AI |

**One trap: say "no" with `ToolError`.** If a tool lets an ordinary error escape, the AI app sees only *"Error executing tool day_summary"*, without the reason. `refused_as_tool_error()` passes on *"no readings for 2026-05-01"* instead.

**The order to run things** (in `code/`):
1. Make sure the data is loaded (Part 2). The MCP tools read the same `readings.db`.
2. `python 6_mcp_server.py http`. Leave it running.
3. In a second terminal:
   - `python 7_list_api_and_tools.py` prints the two lists.
   - `python 8_test_mcp.py` calls every tool. Results:
     - 12 ÷ 3 = 4.0;
     - ÷ 0 comes back with `isError` and the reason;
     - 23 Mar is **106.4 %, OVERLOAD**, the same as REST's `/summary`.
   - `python 9_mcp_on_the_wire.py` sends the four raw messages: `initialize`, `notifications/initialized`, `tools/list`, `tools/call`.

**A UI for the tools** (`10_mcp_ui.py`). With `6_mcp_server.py http` running, run `streamlit run 10_mcp_ui.py`. The page:
- lists the 5 tools, with their inputs and descriptions;
- builds a form for each from its JSON Schema: `enum` becomes a drop-down, an integer with limits becomes a number box, and `format: date` becomes a date picker;
- shows the JSON-RPC `tools/call` it sent, and the result or the refusal with its reason;
- keeps a table of your calls.

Unlike Cursor, here **you** pick the tool. To use another server, run `MCP_URL=http://127.0.0.1:8012/mcp streamlit run 10_mcp_ui.py`.

**Connect Cursor:**
1. With `6_mcp_server.py http` running, copy `cursor_mcp.json` to `.cursor/mcp.json`. It contains `{"mcpServers": {"campus-energy-v2": {"url": "http://127.0.0.1:8002/mcp"}}}`.
2. In Cursor's **Tools & MCP** settings (called **Customize** in newer versions), switch on `campus-energy-v2`. It lists the **5 tools**.
3. In Agent mode, ask *"Was the transformer overloaded on 23 March 2026?"*. Cursor proposes `day_summary`; approve it.
4. Ask it to *"Delete all the readings"*. There's no such tool, so Cursor can't, which is on purpose.

**If it doesn't work:**
- **Red dot:** the server isn't running, or the URL isn't exactly `/mcp` on 8002.
- **To see Cursor's side:** open the Output panel (`Cmd+Shift+U`) and choose **MCP Logs**.
- **Without a terminal:** `cursor_mcp_stdio.json` makes Cursor start `6_mcp_server.py` itself.

**Connect Claude Code** (from `code/`; `.mcp.json` is already there):

```bash
claude mcp add --transport http --scope project campus-energy-v2 http://127.0.0.1:8002/mcp
```

`claude mcp list` shows **Pending approval**, because a project's `.mcp.json` could point anywhere, so Claude Code asks once. Run `claude`, approve `campus-energy-v2`, and ask *"Was the transformer overloaded on 23 March 2026?"*. It asks to run `day_summary`; allow it.

**Testing screens:** the last step of `index.html` shows every part run for real:
- **Swagger `/docs`:** both APIs, plus a GET with Try it out, both uploads and `/summary`.
- **Terminals:** every numbered script.
- **Claude Code:** adding the server, and connected with its 5 tools.

The page also says what to capture in Cursor. All the images are in `assets/img/screens/v2_*.png`.

**To try the tools without an AI:** run `npx -y @modelcontextprotocol/inspector` and connect to `http://127.0.0.1:8002/mcp`.

## Files

```
v2/
  index.html             the student page (built by tools/build_page.py)
  requirements.txt
  code/                  everything students use: the numbered programs, the logic, the two CSV files
  slides/                V2_REST_to_MCP.pptx (24 slides)
  tools/build_page.py    builds index.html and downloads/v2_workshop.zip
  tools/build_deck.js    builds the slides (with actoryx_deck.js and deck_helpers.js, the Actoryx format)
  assets/                the page's style, script and logo (the same as v1's)
```

To rebuild the page after changing any code, run this from `v2/`:

```bash
python tools/build_page.py
```

The CSV data is **generated, not real** (from `v1/data/make_data.py`, with a fixed seed), and contains no client or personal data.
