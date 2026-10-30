// deck_helpers.js — the Actoryx deck helpers (boxes, tables, screenshots, title / problem / close slides),
// the same as v1's tools/build_reactui_decks.js, here so v2 builds on its own.
const fs = require("fs");
const path = require("path");
const AX = require("./actoryx_deck");
const { NAVY, SLATE, GREY, LIGHT, AMBER, CREAM, CREAM2, WHITE, GREEN, BLUE, PURPLE } = AX;

const V2 = path.resolve(__dirname, "..");
const SHOT = (n) => path.join(V2, "assets", "img", "screens", n);
const RED = "C0392B";

function pngSize(file) {                                       // width and height from the PNG header
  const b = fs.readFileSync(file);
  return [b.readUInt32BE(16), b.readUInt32BE(20)];
}

function deck(title) {
  const D = AX.createDeck(title);
  const { pres, oname } = D;
  const seen = new Set();                                    // declare each section once, just before its first slide
  const section = (t) => { if (!seen.has(t)) { seen.add(t); pres.addSection({ title: t }); } };
  const baseContent = D.content;
  D.content = (sec, header) => { section(sec); return baseContent(sec, header); };

  D.box = (s, t, sub, x, y, w, h, fill = SLATE, dark = false, size = 12) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: fill }, line: { color: fill }, objectName: oname("box") });
    const tc = dark ? NAVY : WHITE, sc = dark ? NAVY : LIGHT;
    s.addText(sub ? [{ text: t, options: { bold: true, fontSize: size, color: tc, breakLine: true } }, { text: sub, options: { fontSize: 9.5, color: sc } }]
                  : [{ text: t, options: { bold: true, fontSize: size, color: tc } }],
              { x, y, w, h, align: "center", valign: "middle", margin: 0.06, isTextBox: true, objectName: oname("box-t") });
  };
  D.arrow = (s, x, y, w = 0.4, h = 0.4, text = "→", size = 18) =>
    s.addText(text, { x, y, w, h, fontSize: size, color: GREY, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: oname("arrow") });
  D.note = (s, text, x, y, w, h, fill = CREAM, line = "F6D9A8", size = 10.5) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.05, fill: { color: fill }, line: { color: line }, objectName: oname("note") });
    s.addText(text, { x: x + 0.15, y: y + 0.05, w: w - 0.3, h: h - 0.1, fontSize: size, color: SLATE, valign: "middle", margin: 0, isTextBox: true, objectName: oname("note-t") });
  };
  D.text = (s, t, x, y, w, h, o = {}) =>
    s.addText(t, { x, y, w, h, fontSize: 10.5, color: SLATE, valign: "top", margin: 0, isTextBox: true, objectName: oname("text"), ...o });
  D.bullets = (s, items, x, y, w, h, size = 10.5) =>
    s.addText(items.map((t, i) => ({ text: t, options: { bullet: { indent: 10 }, breakLine: i < items.length - 1 } })),
              { x, y, w, h, fontSize: size, color: SLATE, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true, objectName: oname("bullets") });
  D.cell = (t, o = {}) => ({ text: t, options: { fontSize: 10, color: SLATE, ...o } });
  D.mono = (t, o = {}) => D.cell(t, { fontFace: "Consolas", fontSize: 9, ...o });
  D.hdr = (...ts) => ts.map((t) => ({ text: t, options: { bold: true, color: WHITE, fill: { color: SLATE }, fontSize: 10 } }));
  D.table = (s, rows, x, y, w, colW, rowH = 0.3) =>
    s.addTable(rows, { x, y, w, colW, rowH, border: { type: "solid", pt: 0.5, color: LIGHT }, fill: { color: WHITE }, margin: 0.05,
                       valign: "middle", objectName: oname("table") });
  D.card = (s, x, y, w, h, t, tag, lines, fill = SLATE) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: "F7F8FA" }, line: { color: LIGHT }, objectName: oname("card") });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.62, fill: { color: fill }, line: { color: fill }, objectName: oname("card-band") });
    s.addText([{ text: t, options: { bold: true, fontSize: 13, color: fill === AMBER ? NAVY : WHITE, breakLine: true } },
               { text: tag, options: { fontSize: 9.5, color: fill === AMBER ? NAVY : LIGHT } }],
              { x: x + 0.12, y, w: w - 0.24, h: 0.62, valign: "middle", margin: 0, isTextBox: true, objectName: oname("card-title") });
    D.bullets(s, lines, x + 0.1, y + 0.72, w - 0.2, h - 0.8);
  };
  D.shot = (s, name, x, y, w, h, alt) => {                     // a screenshot, fitted inside the box, with a thin frame
    const file = SHOT(name);
    const [pw, ph] = pngSize(file);
    const k = Math.min(w / pw, h / ph), iw = pw * k, ih = ph * k;
    const ix = x + (w - iw) / 2, iy = y;
    s.addShape(pres.shapes.RECTANGLE, { x: ix - 0.02, y: iy - 0.02, w: iw + 0.04, h: ih + 0.04, fill: { color: LIGHT }, line: { color: LIGHT }, objectName: oname("frame") });
    s.addImage({ path: file, x: ix, y: iy, w: iw, h: ih, altText: alt, objectName: oname("shot") });
    return ih;
  };
  D.js = (s, t, code, x, y, w, h, size = 8.5) => D.codePanel(s, t, code, x, y, w, h, size, "js");
  D.title = (sec, t, sub, chips, footer, notes) => {
    section(sec);
    const s = pres.addSlide({ masterName: "AX_DARK", sectionTitle: sec });
    s.addText(t, { placeholder: "title" });
    s.addText(sub, { placeholder: "sub" });
    const w = 9.4 / chips.length;
    chips.forEach((c, i) => D.chip(s, c, 0.3 + i * w, 4.08, w - 0.1, SLATE, AMBER));
    s.addText(footer, { x: 0.3, y: 5.2, w: 9.4, h: 0.28, fontSize: 9.5, color: GREY, margin: 0, isTextBox: true, objectName: oname("title-footer") });
    s.addNotes(notes);
    return s;
  };
  D.problem = (sec, story, quotes, given, find, rules, steps, notes) => {
    const s = D.content(sec, "PROBLEM STATEMENT  ·  And how we will solve it");
    D.label(s, "The problem", 0.3, 0.72, 5.1);
    D.text(s, story, 0.3, 0.98, 5.1, 0.75);
    s.addText(quotes.map((q, i) => ({ text: q, options: { bullet: { indent: 10 }, breakLine: i < quotes.length - 1 } })),
              { x: 0.3, y: 1.75, w: 5.1, h: 0.6, fontSize: 10.5, italic: true, bold: true, color: NAVY, valign: "top", margin: 0, isTextBox: true, objectName: oname("quotes") });
    const lab = (t) => D.cell(t, { bold: true, color: AMBER, fill: { color: NAVY } });
    D.table(s, [[lab("Given"), D.cell(given, { fontSize: 9.5 })], [lab("Find"), D.cell(find, { fontSize: 9.5 })], [lab("Rules"), D.cell(rules, { fontSize: 9.5 })]],
            0.3, 2.5, 5.1, [0.7, 4.4], 0.55);
    D.label(s, "Solution approach", 5.7, 0.72, 4.0);
    steps.forEach(([t, sub], i) => {
      const y = 0.98 + i * (3.8 / steps.length);
      D.numCircle(s, i + 1, 5.7, y, 0.34);
      D.text(s, [{ text: t, options: { bold: true, color: NAVY, breakLine: true } }, { text: sub, options: { color: GREY, fontSize: 9.5 } }],
             6.15, y - 0.02, 3.55, 0.55, { fontSize: 11 });
    });
    s.addNotes(notes);
    return s;
  };
  D.close = (sec, t, sub, lines, notes) => {
    section(sec);
    const s = pres.addSlide({ masterName: "AX_DARK", sectionTitle: sec });
    s.addText(t, { placeholder: "title" });
    s.addText(sub, { placeholder: "sub" });
    s.addText(lines.map((l, i) => ({ text: l, options: { bullet: { indent: 12 }, breakLine: i < lines.length - 1 } })),
              { x: 0.3, y: 4.0, w: 9.4, h: 1.1, fontSize: 11, color: LIGHT, valign: "top", margin: 0, paraSpaceAfter: 3, isTextBox: true, objectName: oname("close") });
    s.addNotes(notes);
  };
  D.trouble = (sec, rows, notes) => {
    const s = D.content(sec, "TROUBLESHOOTING  ·  What you see, why, and the fix");
    D.table(s, [D.hdr("You see", "Why", "Fix"), ...rows.map(([a, b, c]) => [D.cell(a, { fontSize: 9.5, bold: true }), D.cell(b, { fontSize: 9.5 }), D.cell(c, { fontSize: 9.5 })])],
            0.3, 0.75, 9.4, [3.2, 2.7, 3.5], 0.5);
    D.bottomBox(s, "lab", "First move, always:", "read the terminal and the browser console (F12). The red line names the problem.");
    s.addNotes(notes);
  };
  D.words = (sec, words, questions) => {
    const s = D.content(sec, "KEY WORDS  ·  And check yourself");
    D.label(s, "Words you now know", 0.3, 0.72, 4.6);
    D.table(s, words.map(([w, m]) => [D.cell(w, { bold: true, color: NAVY }), D.cell(m, { fontSize: 9.5 })]), 0.3, 0.98, 4.6, [1.25, 3.35], 0.36);
    D.label(s, "Check yourself (answers in the notes)", 5.2, 0.72, 4.5);
    questions.forEach(([q], i) => {
      D.numCircle(s, i + 1, 5.2, 1.0 + i * 0.75, 0.3);
      D.text(s, q, 5.6, 0.98 + i * 0.75, 4.1, 0.7, { fontSize: 10.5 });
    });
    s.addNotes("Answers:\n" + questions.map(([q, a], i) => `${i + 1}. ${a}`).join("\n"));
  };
  return D;
}

module.exports = { deck, RED, AX };
