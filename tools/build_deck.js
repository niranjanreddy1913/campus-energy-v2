// v2 deck — From a REST API to MCP tools, in the Actoryx format (16:9, navy / amber, Calibri + Consolas).
// Code is read from v2/code and every screenshot is a real run (assets/img/screens/v2_*.png, the page's "Testing screens").
//   node tools/build_deck.js          (from v2/)  →  slides/V2_REST_to_MCP.pptx
const fs = require("fs");
const path = require("path");
const { deck, RED, AX } = require("./deck_helpers");
const { NAVY, SLATE, GREY, LIGHT, AMBER, CREAM, GREEN, WHITE } = AX;

const V2 = path.resolve(__dirname, "..");
const CODE = path.join(V2, "code");
const OUT = path.join(V2, "slides", "V2_REST_to_MCP.pptx");

// ── code snippets, straight from the files ─────────────────────────────────────────────────────────
const read = (f) => fs.readFileSync(path.join(CODE, f), "utf8").split("\n");
function between(lines, start, stop) {
  const a = lines.findIndex((l) => l.includes(start));
  if (a < 0) throw new Error(`marker not found: ${start}`);
  const b = stop ? lines.findIndex((l, i) => i > a && l.includes(stop)) : lines.length;
  return lines.slice(a, b < 0 ? lines.length : b);
}
function noDocstrings(ls) {                                        // drop """…""" blocks (one line or several): the slide shows the code
  const out = [];
  let inDoc = false;
  for (const l of ls) {
    const n = (l.match(/"""/g) || []).length;
    if (inDoc) { if (n) inDoc = false; continue; }
    if (n === 1) { inDoc = true; continue; }
    if (n >= 2 && l.trim().startsWith('"""')) continue;
    out.push(l);
  }
  return out;
}
const tidy = (ls) => noDocstrings(ls).map((l) => l.replace(/\s{2,}#.*$/, "")).join("\n").replace(/\n{3,}/g, "\n\n").trim();
const CALC = tidy(between(read("calculator.py"), "def calculate(", "if __name__").filter((l) => !l.trim().startsWith('"""')));
const API1 = tidy(between(read("1_calculator_api.py"), "@app.get(\"/calculate\")", "# ── 2 · POST"));
const UPLOAD = tidy(between(read("3_readings_api.py"), "@app.post(\"/readings/upload\"", "@app.delete("))
  .replace(/description="[^"]*"/g, "description=…");                                  // the descriptions are in /docs; here, the shape
const SUMMARY_REST = tidy(between(read("3_readings_api.py"), "@app.get(\"/summary\")", "@app.get(\"/peak-days\")").filter((l) => !l.trim().startsWith('"""')));
const SUMMARY_MCP = tidy(between(read("6_mcp_server.py"), "def day_summary(", "@mcp.tool()").filter((l) => !l.trim().startsWith('"""')));
const MCP_HEAD = tidy(between(read("6_mcp_server.py"), 'mcp = MCPServer("', "# ── From Part 1"));

async function main() {
  const D = deck("From a REST API to MCP Tools — MGIT Workshop v2");
  const { content, label, bottomBox, numCircle, chip, box, arrow, note, text, bullets, cell, mono, hdr, table, card, shot } = D;
  const py = (s, t, code, x, y, w, h, size = 8.5) => D.codePanel(s, t, code, x, y, w, h, size);
  const ok = (t) => cell(t, { bold: true, color: GREEN });
  const no = (t) => cell(t, { bold: true, color: RED });
  let s;

  // ═══════════════════════════════════ Opening ═══════════════════════════════════
  D.title("Opening", "From a REST API to MCP Tools",
    "MGIT Workshop v2 · build two REST APIs, then open the same logic to AI apps (Cursor, Claude Code)",
    ["Part 1 · Calculator API", "Part 2 · Readings API", "Part 3 · MCP server", "Cursor · Claude Code"],
    "Actoryx Technologies  ·  MGIT Centre of Excellence in AI  ·  everything runs on a laptop; every screen in this deck is a real run",
    "One idea all session: write the logic once, give it many doors. REST is the door for people and programs; MCP is the door for AI apps.");

  D.problem("Opening",
    "Everyone needs quick calculations, and the substation's meter readings arrive as a CSV. People — and now AI apps — need answers without opening a spreadsheet:",
    ["“What is 12 divided by 3?”", "“Was transformer TR-MAIN overloaded on 23 March 2026?”"],
    "a calculator function · campus_feb_mar_2026.csv (5,664 readings, every 15 min, 1 Feb – 31 Mar 2026)",
    "a REST API for each (people and programs), then the same functions as MCP tools (Cursor, Claude Code)",
    "logic in plain functions · every input checked · every CSV row checked · AI gets read-only tools",
    [["Calculator API", "GET / POST /calculate · status codes"], ["Readings API", "upload the CSV through the API"], ["Ask questions", "/summary · /peak-days · /readings"],
     ["MCP server", "the same functions as 5 tools"], ["AI apps", "Cursor and Claude Code call them"]],
    "Read the problem. Ask: who reads /docs? (a person). Who can't? (an AI app) — that's why Part 3 exists.");

  s = content("Opening", "THE PLAN  ·  Write the logic once, give it many doors");
  [["calculator.py", "readings.py — the logic", AMBER, true], ["1_ · 3_ …_api.py", "REST: /docs", SLATE, false], ["6_mcp_server.py", "MCP: 5 tools", AMBER, true],
   ["Browser · Cursor", "Claude Code · programs", SLATE, false]].forEach(([t, sub, fill, dark], i) => {
    box(s, t, sub, 0.3 + i * 2.4, 0.8, 2.1, 0.78, fill, dark, 12);
    if (i < 3) arrow(s, 2.42 + i * 2.4, 0.99, 0.25, 0.4, "→", 16);
  });
  table(s, [hdr("Part", "What we build", "The new idea"),
    [cell("1 · Calculator API", { bold: true }), cell("two numbers + one operation → the answer"), cell("GET and POST, query vs JSON body, /docs, 200 · 400 · 422")],
    [cell("2 · Readings API", { bold: true }), cell("upload 5,664 readings through the API, then ask"), cell("file upload, checking every row, SQLite, 404")],
    [cell("3 · MCP", { bold: true }), cell("the same two APIs as MCP tools, in Cursor and Claude Code"), cell("tools an AI app discovers and calls")]],
    0.3, 1.85, 9.4, [1.9, 3.7, 3.8], 0.42);
  note(s, "The rule: calculator.py and readings.py have NO web code. The API files only receive a request, call a function and return its answer — so in Part 3 the MCP server imports the very same functions.", 0.3, 3.75, 9.4, 0.7);
  bottomBox(s, "lab", "Set up once:", "pip install -r requirements.txt  (fastapi, uvicorn, python-multipart, sqlalchemy, pandas, httpx, mcp)  ·  then cd code");
  s.addNotes("Show the three columns of the flow: logic, REST door, MCP door. Nothing in the logic changes when we add a door.");

  s = content("Opening", "WHICH FILE DO I RUN?  ·  One folder, code/ — the numbers are the order");
  table(s, [hdr("File", "What it is", "Run"),
    [mono("1_calculator_api.py"), cell("Part 1 · the calculator REST API — port 8000"), mono("python 1_calculator_api.py")],
    [mono("2_test_calculator.py"), cell("Part 1 · every case, against the running API"), mono("python 2_test_calculator.py")],
    [mono("3_readings_api.py"), cell("Part 2 · the readings REST API — port 8001"), mono("python 3_readings_api.py")],
    [mono("4_upload_csv.py"), cell("Part 2 · uploads the CSV to the running API"), mono("python 4_upload_csv.py")],
    [mono("5_test_readings.py"), cell("Part 2 · every endpoint, including refusals"), mono("python 5_test_readings.py")],
    [mono("6_mcp_server.py"), cell("Part 3 · the same logic as 5 MCP tools — port 8002"), mono("python 6_mcp_server.py http")],
    [mono("7_ · 8_ · 9_ · 10_"), cell("Part 3 · the two lists · test every tool · the wire · a UI"), mono("streamlit run 10_mcp_ui.py")],
    [mono("calculator.py, readings.py, db.py"), cell("the logic — imported, so no number (Python can't import 1_…)"), cell("read them", { bold: true })]],
    0.3, 0.75, 9.4, [2.75, 4.0, 2.65], 0.38);
  bottomBox(s, "lab", "Ports:", "calculator 8000 · readings 8001 · MCP 8002 — all three can run at once. Busy? python 1_calculator_api.py 8010 and API_URL=… for its test.");
  s.addNotes("A file name can't start with a digit for `import`, so the imported logic files keep plain names. uvicorn and importlib can load the numbered ones.");

  // ═══════════════════════════════════ Part 1 ═══════════════════════════════════
  s = content("Part 1 · Calculator API", "PART 1  ·  The logic, then a web address for it");
  py(s, "calculator.py — the logic, no web code", CALC, 0.3, 0.75, 4.55, 3.95, 8.5);
  py(s, "1_calculator_api.py — the REST door", API1, 5.15, 0.75, 4.55, 2.35, 8.5);
  note(s, "@app.get(\"/calculate\") gives the function an address. op: Literal[...] allows only four words. A ValueError from our function becomes HTTP 400 with its reason.", 5.15, 3.2, 4.55, 1.5);
  bottomBox(s, "lab", "Run:", "python 1_calculator_api.py  →  http://127.0.0.1:8000/calculate?a=12&b=3&op=div  and  /docs");
  s.addNotes("POST /calculate takes the same inputs as a JSON body {\"a\":12,\"b\":3,\"op\":\"div\"} — the exact shape an MCP tool's arguments will have in Part 3.");

  s = content("Part 1 · Calculator API", "PART 1  ·  /docs — FastAPI wrote it from the code; Try it out");
  shot(s, "v2_calc_docs.png", 0.3, 0.75, 4.4, 2.0, "Calculator API /docs");
  text(s, "http://127.0.0.1:8000/docs — GET and POST /calculate", 0.3, 2.85, 4.4, 0.3, { fontSize: 9.5, color: GREY });
  shot(s, "v2_calc_try.png", 5.0, 0.75, 4.7, 4.0, "GET /calculate executed: 12 div 3 = 4");
  bottomBox(s, "lab", "Try it:", "GET /calculate → Try it out → a = 12, b = 3, op = div → Execute → 200, \"result\": 4", 0.3, 4.4);
  s.addNotes("Point out the curl line Swagger prints — the same request a program would send.");

  s = content("Part 1 · Calculator API", "PART 1  ·  Three answers: 200, 400, 422 — and who said no");
  table(s, [hdr("Status", "Means", "Who said no"),
    [ok("200 OK"), cell("here is the answer"), cell("—")],
    [no("400 Bad request"), cell("the request was fine; the values can't be done (1 ÷ 0)"), cell("our function (ValueError → HTTPException)")],
    [no("422 Unprocessable"), cell("the request broke the rules (op=pow, a=twelve, b missing)"), cell("FastAPI — our code never ran")]],
    0.3, 0.75, 9.4, [1.8, 4.4, 3.2], 0.4);
  shot(s, "v2_term_2_test_calculator.png", 0.3, 2.45, 9.4, 2.35, "python 2_test_calculator.py output");
  s.addNotes("Run it live in a second terminal with the API running. The first line proves which API it is testing.");

  // ═══════════════════════════════════ Part 2 ═══════════════════════════════════
  s = content("Part 2 · Readings API", "PART 2  ·  The data — and the upload checks every row");
  table(s, [hdr("Column", "Meaning", "Range"),
    [mono("timestamp"), cell("every 15 minutes"), cell("1 Feb – 31 Mar 2026")], [mono("load_kw"), cell("the whole campus"), cell("162 – 891 kW")],
    [mono("solar_kw"), cell("rooftop solar"), cell("0 – 384 kW")], [mono("ambient_c"), cell("air temperature"), cell("11.5 – 38.9 °C")],
    [mono("irradiance_wm2"), cell("sunlight on the panels"), cell("0 – 1,049 W/m²")]], 0.3, 0.75, 5.0, [1.5, 1.85, 1.65], 0.36);
  label(s, "readings_with_problems.csv: 9 rows → 3 loaded, 6 refused", 5.6, 0.75, 4.1);
  bullets(s, ["line 4 · solar_kw 'abc' is not a number", "line 5 · 2026-02-30 is not a real date", "line 6 · solar_kw −15 is outside 0–500",
              "line 7 · ambient_c 80 is outside −10–55", "line 8 · duplicate time", "line 9 · load_kw is empty"], 5.6, 1.05, 4.1, 2.1, 10);
  note(s, "Transformer loading = (load − solar) ÷ 0.93 ÷ 630 kVA  →  NORMAL · HIGH (> 80 %) · OVERLOAD (> 100 %). Generated data, fixed seed — no client or personal data.", 0.3, 3.15, 9.4, 0.7);
  bottomBox(s, "lab", "Whole-file refusals (400):", "not a .csv · missing columns. Upload again with replace=false → 0 added, 5,664 already there.");
  s.addNotes("Every row is checked; good rows are stored, every refused row comes back with its line number and reason.");

  s = content("Part 2 · Readings API", "PART 2  ·  Six endpoints — upload, delete, and four that answer");
  table(s, [hdr("Method", "Endpoint", "Inputs", "What it does"),
    [mono("POST"), mono("/readings/upload"), cell("a CSV file, replace"), cell("load the file — every row checked; returns a report")],
    [mono("GET"), mono("/readings/stats"), cell("—"), cell("how many readings, from when to when")],
    [mono("GET"), mono("/readings"), cell("start, end"), cell("the raw rows — at most 7 days")],
    [mono("GET"), mono("/summary"), cell("day"), cell("one day: peak load, energy, solar, loading %, status")],
    [mono("GET"), mono("/peak-days"), cell("top (1–31)"), cell("the hardest-working days")],
    [mono("DELETE"), mono("/readings"), cell("—"), cell("remove everything")]], 0.3, 0.75, 5.1, [0.75, 1.45, 1.1, 1.8], 0.42);
  py(s, "3_readings_api.py — the upload endpoint (descriptions folded: …)", UPLOAD, 5.6, 0.75, 4.1, 3.95, 8);
  bottomBox(s, "lab", "Run:", "python 3_readings_api.py  →  http://127.0.0.1:8001/docs   (port 8001, next to the calculator on 8000)");
  s.addNotes("404 = no data that day (readings.NotFound); 400 = the request can't be done (ValueError) — the answer() helper maps them.");

  s = content("Part 2 · Readings API", "PART 2  ·  Load the data THROUGH the API — Choose file in /docs");
  shot(s, "v2_read_upload_problems.png", 0.3, 0.75, 4.6, 4.0, "Upload of readings_with_problems.csv: 3 loaded, 6 refused");
  shot(s, "v2_read_upload.png", 5.1, 0.75, 4.6, 3.6, "Upload of campus_feb_mar_2026.csv: 5,664 loaded");
  text(s, "Left: the problem file → 201, 3 loaded, 6 refused with reasons.  Right: the real file → 5,664 loaded, 1 Feb → 31 Mar.", 5.1, 4.42, 4.6, 0.45, { fontSize: 9.5, color: GREY });
  s.addNotes("Also from a program: python 4_upload_csv.py — or curl -F \"file=@campus_feb_mar_2026.csv\" http://127.0.0.1:8001/readings/upload");

  s = content("Part 2 · Readings API", "PART 2  ·  Ask: 23 March → 106.4 %, OVERLOAD — and test every endpoint");
  shot(s, "v2_read_summary.png", 0.3, 0.75, 4.4, 3.9, "GET /summary 2026-03-23");
  shot(s, "v2_term_5_test_readings.png", 4.9, 0.75, 4.8, 3.9, "python 5_test_readings.py output");
  bottomBox(s, "lab", "Statuses here:", "201 upload accepted · 400 not .csv / wrong columns / > 7 days · 404 no readings that day · 422 top=0");
  s.addNotes("5_test_readings.py empties the database first and ends with the 5,664 readings loaded again.");

  // ═══════════════════════════════════ Part 3 ═══════════════════════════════════
  s = content("Part 3 · MCP", "PART 3  ·  What we ADD to make it MCP — one file, one library");
  table(s, [hdr("", "REST (1_, 3_)", "MCP (6_mcp_server.py)"),
    [cell("Library", { bold: true }), mono("fastapi · uvicorn"), mono("+ mcp")],
    [cell("Server object", { bold: true }), mono("app = FastAPI(...)"), mono('mcp = MCPServer("campus-energy-v2")')],
    [cell("Publish a function", { bold: true }), mono('@app.get("/summary") — method + URL'), mono("@mcp.tool() — just a name")],
    [cell("Inputs and limits", { bold: true }), cell("type hints · Query · Literal"), ok("the SAME type hints + Field(description)")],
    [cell("What a client reads", { bold: true }), cell("/docs — for a person"), cell("tools/list — name, docstring, JSON Schema")],
    [cell("The docstring", { bold: true }), cell("optional"), cell("essential: all the AI knows")],
    [cell("Saying “no”", { bold: true }), mono("HTTPException(400 / 404)"), mono("ToolError → isError + reason")],
    [cell("Start the web server", { bold: true }), mono("uvicorn.run(app, port=8001)"), mono('mcp.run(transport="streamable-http", port=8002)')]], 0.3, 0.75, 9.4, [1.8, 3.4, 4.2], 0.42);
  bottomBox(s, "lab", "Unchanged:", "calculator.py, readings.py, db.py. The MCP server imports them — nothing is copied.");
  s.addNotes("The question: what does an AI app need that a person reading /docs doesn't? A way to ASK the server what it can do. That's MCP. " +
    "Last row: transport=\"streamable-http\" is what opens port 8002 at /mcp. mcp.run() alone means stdio: no port, the AI app starts the server and talks through stdin/stdout.");

  s = content("Part 3 · MCP", "PART 3  ·  Each read endpoint becomes a named tool — the two that change data don't");
  table(s, [hdr("REST endpoint", "MCP tool", "Same function"),
    [mono("GET · POST /calculate"), mono("calculate"), mono("calculator.calculate")], [mono("GET /readings/stats"), mono("readings_stats"), mono("readings.stats")],
    [mono("GET /readings"), mono("get_readings"), mono("readings.get_readings")], [mono("GET /summary"), mono("day_summary"), mono("readings.summary")],
    [mono("GET /peak-days"), mono("peak_days"), mono("readings.peak_days")],
    [mono("POST /readings/upload · DELETE /readings"), no("— REST only"), cell("they change data: a person does that")]], 0.3, 0.75, 5.4, [2.25, 1.35, 1.8], 0.42);
  py(s, "6_mcp_server.py — the server and how it says no", MCP_HEAD, 5.95, 0.75, 3.75, 3.95, 7.5);
  bottomBox(s, "lab", "Why ToolError?", "any other error reaches the AI only as “Error executing tool” — without the reason.");
  s.addNotes("REST says WHAT with the method and WHICH with the URL; MCP says both with the tool's name.");

  s = content("Part 3 · MCP", "PART 3  ·  Same function, two doors — /summary and day_summary");
  py(s, "3_readings_api.py — REST", SUMMARY_REST, 0.3, 0.75, 4.55, 1.9, 8.5);
  py(s, "6_mcp_server.py — MCP", SUMMARY_MCP, 5.15, 0.75, 4.55, 1.9, 8);
  shot(s, "v2_term_6_mcp_server.png", 0.3, 2.85, 9.4, 0.7, "python 6_mcp_server.py http");
  note(s, "Both call readings.summary(day). REST turns NotFound into 404; MCP turns it into a ToolError the AI can read: “no readings for 2026-05-01”.", 0.3, 3.75, 9.4, 0.65);
  bottomBox(s, "lab", "Run:", "python 6_mcp_server.py (or PyCharm ▶)  →  http://127.0.0.1:8002/mcp   ·   python 6_mcp_server.py stdio is only for an AI app that starts it");
  s.addNotes("Start the MCP server in terminal 1 and leave it running for the next slides. Load the data first (Part 2): the tools read the same readings.db.");

  s = content("Part 3 · MCP", "PART 3  ·  The two lists — 9 REST endpoints, 5 MCP tools");
  shot(s, "v2_term_7_list.png", 0.3, 0.75, 9.4, 4.05, "python 7_list_api_and_tools.py output");
  s.addNotes("7_list_api_and_tools.py reads both lists from the code itself — app.openapi() for REST, tools/list for MCP — so they can't go out of date.");

  s = content("Part 3 · MCP", "PART 3  ·  Test every tool, as an AI app would — REST and MCP agree");
  shot(s, "v2_term_8_test_mcp.png", 0.3, 0.75, 6.4, 4.05, "python 8_test_mcp.py output");
  table(s, [hdr("REST says", "MCP says"), [cell("200 + JSON"), cell("isError: false + result")], [cell("400 / 404 — our function refused"), cell("isError: true + the reason")],
    [cell("422 — broke the rules"), cell("isError: true — the schema refused")]], 6.9, 0.75, 2.8, [1.4, 1.4], 0.55);
  note(s, "Last line: REST /summary and MCP day_summary give 106.4 % OVERLOAD — one function, two doors.", 6.9, 3.15, 2.8, 1.1, CREAM, "F6D9A8", 9.5);
  s.addNotes("8_test_mcp.py first checks the server's name is campus-energy-v2 — the old Day 5 server on 8002 is refused with a clear message.");

  s = content("Part 3 · MCP", "PART 3  ·  MCP on the wire — four JSON-RPC messages, each an HTTP POST to /mcp");
  [["① initialize", "agree the protocol; get mcp-session-id (a response HEADER)"], ["② initialized", "a notification — no id, HTTP 202"],
   ["③ tools/list", "every tool's name, description, JSON Schema"], ["④ tools/call", "run one tool with its arguments → result + isError"]].forEach(([t, sub], i) => {
    box(s, t, sub, 0.3, 0.8 + i * 0.95, 3.2, 0.82, i === 3 ? AMBER : NAVY, i === 3, 11);
  });
  shot(s, "v2_term_9_wire.png", 3.75, 0.75, 5.95, 4.05, "python 9_mcp_on_the_wire.py output");
  s.addNotes("Client(...), Cursor and Claude Code all send exactly these four. Without the session id the server answers HTTP 400. Over stdio there's no session header: the process is the session.");

  s = content("Part 3 · MCP", "AI APPS  ·  Connect Cursor — and see all five tools");
  [["Start", "python 6_mcp_server.py http (and load the data in Part 2)"], ["Config", ".cursor/mcp.json is already in code/ → url http://127.0.0.1:8002/mcp"],
   ["See the tools", "Settings → Tools & MCP (or Customize): campus-energy-v2 ● green, 5 tools"],
   ["Ask", "Agent chat: “Was the transformer overloaded on 23 March 2026?” → day_summary → approve → 106.4 %, OVERLOAD"],
   ["Can't", "“Delete all the readings” — no such tool, so Cursor can't. On purpose."]].forEach(([t, sub], i) => {
    numCircle(s, i + 1, 0.3, 0.8 + i * 0.72);
    text(s, [{ text: t + "   ", options: { bold: true, color: NAVY } }, { text: sub, options: { color: SLATE } }], 0.8, 0.82 + i * 0.72, 5.0, 0.62, { fontSize: 10.5 });
  });
  py(s, ".cursor/mcp.json", fs.readFileSync(path.join(CODE, ".cursor", "mcp.json"), "utf8").trim(), 6.1, 0.8, 3.6, 1.75, 9);
  note(s, "No terminal? cursor_mcp_stdio.json: Cursor starts 6_mcp_server.py itself (stdio). Red dot? The server isn't running, or the URL isn't exactly /mcp. Logs: Cmd+Shift+U → MCP Logs.", 6.1, 2.7, 3.6, 1.6, CREAM, "F6D9A8", 9.5);
  bottomBox(s, "lab", "Students capture:", "the Tools & MCP list · the day_summary call card (click the arrow for its arguments) · the answer");
  s.addNotes("Cursor asks before running a tool by default — the approval step is where students see the arguments the model filled in.");

  s = content("Part 3 · MCP", "AI APPS  ·  Claude Code — the same server, from a project .mcp.json");
  shot(s, "v2_term_claude_code.png", 0.3, 0.75, 5.6, 2.45, "claude mcp add, .mcp.json, claude mcp get");
  shot(s, "v2_term_claude_code_tools.png", 0.3, 3.3, 5.6, 1.5, "Claude Code connected: 5 tools");
  label(s, "Three commands, in code/", 6.15, 0.75, 3.55);
  bullets(s, ["claude mcp add --transport http --scope project campus-energy-v2 http://127.0.0.1:8002/mcp",
              "claude mcp list → Pending approval (a project's .mcp.json could point anywhere, so it asks once)",
              "claude → approve → “Was the transformer overloaded on 23 March 2026?” → allow day_summary"], 6.15, 1.05, 3.55, 2.6, 9.5);
  note(s, "Tools appear as mcp__campus-energy-v2__day_summary etc. .mcp.json ships with the folder, so every student gets the server.", 6.15, 3.7, 3.55, 1.1, CREAM, "F6D9A8", 9.5);
  s.addNotes("The answer screenshot needs a signed-in Claude Code; students capture it after approving the server.");

  s = content("Part 3 · MCP", "A UI FOR THE TOOLS  ·  10_mcp_ui.py — list every tool, call it from a form");
  shot(s, "v2_ui_tools.png", 0.3, 0.75, 5.6, 4.05, "Streamlit MCP UI: the tools, and day_summary called");
  label(s, "streamlit run 10_mcp_ui.py", 6.15, 0.75, 3.55);
  bullets(s, ["Lists the tools with tools/list — names, inputs, descriptions", "Builds each form from the tool's JSON Schema: enum → drop-down, integer + min/max → number box, date → date picker",
              "Calls with tools/call; shows the JSON-RPC message, then the result — or isError and the reason", "Works with ANY MCP server: change the URL in the sidebar"], 6.15, 1.05, 3.55, 2.75, 9.5);
  note(s, "Cursor: the MODEL picks the tool. This page: YOU pick it — the same two messages either way.", 6.15, 3.9, 3.55, 0.85, CREAM, "F6D9A8", 9.5);
  s.addNotes("Start 6_mcp_server.py http first. Try a refusal live: calculate with b = 0, or get_readings for more than 7 days.");

  s = content("Part 3 · MCP", "REST vs MCP  ·  The difference in the UI — you pick the endpoint, or the model picks the tool");
  card(s, 0.3, 0.8, 4.55, 3.4, "REST · /docs (Swagger)", "for people and programs", [
    "The list: endpoints by URL and method", "YOU pick the endpoint, fill the boxes, press Execute", "Back: a status code (200 · 400 · 404 · 422) and JSON",
    "Clients: browser, Streamlit, React, curl, any program"], SLATE);
  card(s, 5.15, 0.8, 4.55, 3.4, "MCP · Cursor / Claude Code", "for AI apps", [
    "The list: tool names + descriptions (tools/list)", "YOU type a sentence; the MODEL picks the tool and fills it; you approve",
    "Back: a result with isError; the model puts it in words", "Try it without an AI: MCP Inspector → http://127.0.0.1:8002/mcp"], AMBER);
  bottomBox(s, "app", "Same functions behind both:", "calculator.py and readings.py — the doors differ, the answers don't (23 Mar = 106.4 % either way).");
  s.addNotes("That is why the docstring matters so much in MCP: the model chooses from it.");

  // ═══════════════════════════════════ Close ═══════════════════════════════════
  D.trouble("Close", [
    ["✗ Nothing is running at …:8001", "the API isn't started", "python 3_readings_api.py (terminal 1)"],
    ["✗ … is not the Readings API", "another program is on that port", "stop it, or use another port + API_URL"],
    ["✗ MCP server … is 'campus-energy', not campus-energy-v2", "an older MCP server holds 8002", "stop it; python 6_mcp_server.py http"],
    ["Console says “stdio”; :8002 not reachable", "started as stdio — it waits on stdin, no port", "run it with no argument (or http); stdio is for AI apps"],
    ["No module named 'mcp'", "this Python lacks the library", "pip install -r requirements.txt (in the Python you run)"],
    ["Claude Code: Pending approval", "project servers need a one-time yes", "run claude, approve campus-energy-v2"],
    ["readings_stats → 0", "the data isn't loaded", "Part 2: python 4_upload_csv.py"]],
    "Every client checks WHO is on the port before sending anything — read its one-line message first.");

  D.words("Close", [["REST API", "functions at web addresses, for people & programs"], ["/docs", "FastAPI's page to try every endpoint"],
    ["Status code", "200 ok · 400 refused · 404 no data · 422 bad request"], ["Upload", "a file sent with POST (multipart)"], ["MCP", "how an AI app discovers and calls tools"],
    ["Tool", "a function with a name, description, schema"], ["ToolError", "MCP's “no, because…”"], ["JSON-RPC", "the 4 messages: initialize … tools/call"]],
    [["What do we ADD to make REST logic available to Cursor?", "One file (6_mcp_server.py) and the mcp library; the logic is imported, not copied."],
     ["GET /calculate?a=1&b=0&op=div → 400. Who said no?", "Our calculate() function (ValueError → HTTPException 400)."],
     ["Why are upload and delete NOT MCP tools?", "They change data — give an AI only what it needs."],
     ["day_summary for 2026-05-01 — what comes back?", "isError: true and “no readings for 2026-05-01” (a ToolError)."],
     ["23 March via REST and via MCP?", "106.4 %, OVERLOAD — the same function behind both."]]);

  D.close("Close", "One Logic, Two Doors", "REST for people and programs · MCP for AI apps — the same calculator.py and readings.py behind both",
    ["Part 1: a calculator API — GET and POST, /docs, 200 · 400 · 422", "Part 2: 5,664 readings uploaded through the API, every row checked; /summary, /peak-days",
     "Part 3: the same functions as 5 MCP tools — tested, on the wire, in Cursor and Claude Code"],
    "Student page: v2/index.html (17 steps, ending with the testing screens).");

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  await AX.save(D.pres, OUT);
}

main();
