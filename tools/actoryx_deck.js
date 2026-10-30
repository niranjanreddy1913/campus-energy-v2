// actoryx_deck.js — the Actoryx slide format, the same format as the v1 workshop decks (16:9, navy / amber, Calibri + Consolas).
//   const AX = require("./actoryx_deck");  const { pres, label, item, ... } = AX.createDeck("Deck title");  …  await AX.save(pres, out);
const path = require("path");
const pptxgen = require("pptxgenjs");

const V2 = path.resolve(__dirname, "..");
const LOGO = path.join(V2, "assets", "img", "actoryx-logo-tile.png");

// ── Actoryx palette (from the Actoryx FastAPI deck) ────────────────────────────────────────────────
const NAVY = "1A2535", SLATE = "2D3748", SLATE2 = "4A5568", GREY = "718096", LIGHT = "E2E8F0",
  AMBER = "F59E0B", CREAM = "FFF8E7", CREAM2 = "FEF3C7", INDIGO_TINT = "EEF2FF", WHITE = "FFFFFF",
  GREEN = "0F6E56", BLUE = "185FA5", PURPLE = "534AB7", CODE_GREEN = "68D391";
const THEME = {
  name: "Actoryx", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: NAVY, lt1: WHITE, dk2: SLATE, lt2: "F7F8FA", accent1: AMBER, accent2: SLATE2, accent3: GREY,
            accent4: CODE_GREEN, accent5: LIGHT, accent6: CREAM, hlink: BLUE, folHlink: PURPLE },
};


function createDeck(title) {
  // ── deck + layouts ─────────────────────────────────────────────────────────────────────────────────
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";                                         // 10 × 5.625 in, as the Actoryx deck
  pres.author = "Actoryx Technologies";
  pres.company = "Actoryx Technologies";
  pres.title = title;
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "AX_DARK",
    background: { color: NAVY },
    objects: [
      { rect: { x: 0, y: 0, w: 0.09, h: 5.625, fill: { color: AMBER } } },
      { ellipse: { x: 9.2, y: 0.12, w: 0.32, h: 0.32, fill: { color: AMBER } } },
      { ellipse: { x: 9.54, y: 0.3, w: 0.2, h: 0.2, fill: { color: AMBER } } },
      { ellipse: { x: 9.76, y: 0.44, w: 0.12, h: 0.12, fill: { color: GREY } } },
      { ellipse: { x: 9.87, y: 0.54, w: 0.07, h: 0.07, fill: { color: GREY } } },
      { image: { path: LOGO, x: 0.3, y: 0.25, w: 3.1, h: 2.07 } },
      { rect: { x: 0.3, y: 2.5, w: 9.4, h: 0.012, fill: { color: AMBER } } },
      { placeholder: { options: { name: "title", type: "title", x: 0.3, y: 2.6, w: 9.4, h: 0.8, fontSize: 30, bold: true,
                                  color: WHITE, align: "left", valign: "middle", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "sub", type: "body", x: 0.3, y: 3.42, w: 9.4, h: 0.45, fontSize: 14, color: AMBER,
                                  valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "AX_CONTENT",
    background: { color: WHITE },
    margin: [0.7, 0.3, 0.3, 0.3],
    objects: [
      { rect: { x: 0, y: 0, w: 10, h: 0.58, fill: { color: NAVY } } },
      { image: { path: LOGO, x: 0.2, y: 0.015, w: 0.825, h: 0.55 } },
      { placeholder: { options: { name: "header", type: "title", x: 1.2, y: 0.1, w: 8.5, h: 0.38, fontSize: 13, bold: true,
                                  color: AMBER, align: "left", valign: "middle", margin: 0 }, text: "" } },
    ],
    slideNumber: { x: 9.35, y: 5.38, w: 0.4, h: 0.2, fontSize: 8, color: GREY, align: "right" },
  });

  // ── helpers in the Actoryx style ───────────────────────────────────────────────────────────────────
  let n = 0;
  const oname = (k) => `${k}-${++n}`;
  function label(s, text, x, y, w) {
    s.addText(text.toUpperCase(), { x, y, w, h: 0.24, fontSize: 9, bold: true, color: GREY, charSpacing: 1.5, margin: 0,
                                    isTextBox: true, objectName: oname("label") });
  }
  function item(s, x, y, w, title, sub) {                       // orange square + dark title + grey line under it
    s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.08, w: 0.09, h: 0.09, fill: { color: AMBER }, line: { color: AMBER },
                                        objectName: oname("dot") });
    s.addText([{ text: title, options: { bold: true, color: SLATE, fontSize: 12, breakLine: true } },
               { text: sub, options: { color: GREY, fontSize: 10 } }],
              { x: x + 0.18, y, w: w - 0.18, h: 0.5, valign: "top", margin: 0, paraSpaceAfter: 1, isTextBox: true,
                objectName: oname("item") });
  }
  function codePanel(s, title, code, x, y, w, h, fontSize = 9, lang = "py") {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: NAVY }, line: { color: NAVY },
                                                objectName: oname("code-bg") });
    s.addText(title, { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: 0.24, fontSize: 9.5, bold: true, color: AMBER, margin: 0,
                       isTextBox: true, objectName: oname("code-title") });
    const runs = code.split("\n").map((line, i, all) => {
      const t = line.trimStart();
      const color = lang === "js"                                // JavaScript / JSX (the ReactUI decks)
        ? (t.startsWith("//") || t.startsWith("{/*") ? GREY : (/^(import|export|const|let|function|return|if|try|catch|await|async)\b/.test(t) ? CODE_GREEN : (t.startsWith("<") ? AMBER : LIGHT)))
        : (t.startsWith("#") ? GREY : (t.startsWith("@") ? AMBER : (/^(def|class|return|raise|if|try|except|global)\b/.test(t) ? CODE_GREEN : LIGHT)));
      return { text: line || " ", options: { color, breakLine: i < all.length - 1 } };
    });
    s.addText(runs, { x: x + 0.15, y: y + 0.36, w: w - 0.3, h: h - 0.44, fontFace: "Consolas", fontSize, valign: "top",
                      margin: 0, lineSpacingMultiple: 1.05, isTextBox: true, objectName: oname("code") });
  }
  function bottomBox(s, kind, lead, text, x = 0.3, w = 9.4) {  // "Lab:" (cream) or "App evolves:" (indigo tint)
    const fill = kind === "lab" ? CREAM : INDIGO_TINT;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.92, w, h: 0.42, rectRadius: 0.05, fill: { color: fill },
                                                line: { color: kind === "lab" ? "F6D9A8" : "D5DCF5" }, objectName: oname(kind) });
    s.addText([{ text: lead + "  ", options: { bold: true, color: SLATE } }, { text, options: { color: kind === "lab" ? SLATE : GREY } }],
              { x: x + 0.15, y: 4.93, w: w - 0.3, h: 0.4, fontSize: 10.5, valign: "middle", margin: 0, isTextBox: true, objectName: oname(kind + "-t") });
  }
  function numCircle(s, num, x, y, d = 0.36) {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: AMBER }, line: { color: AMBER }, objectName: oname("num") });
    s.addText(String(num), { x, y, w: d, h: d, fontSize: d > 0.3 ? 13 : 10, bold: true, color: NAVY, align: "center", valign: "middle",
                             margin: 0, isTextBox: true, objectName: oname("num-t") });
  }
  function chip(s, text, x, y, w, fill = SLATE, color = LIGHT, fontSize = 9.5) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 0.3, rectRadius: 0.05, fill: { color: fill }, line: { color: fill },
                                                objectName: oname("chip") });
    s.addText(text, { x, y, w, h: 0.3, fontSize, bold: true, color, align: "center", valign: "middle", margin: 0, isTextBox: true,
                      objectName: oname("chip-t") });
  }
  const content = (section, header) => {
    const s = pres.addSlide({ masterName: "AX_CONTENT", sectionTitle: section });
    s.addText(header, { placeholder: "header" });
    return s;
  };


  return { pres, C, label, item, codePanel, bottomBox, numCircle, chip, content, oname };
}

async function save(pres, out) {
  await pres.writeFile({ fileName: out });
  if (process.env.PPTX_SKILL) {
    const { applyTheme } = require(path.join(process.env.PPTX_SKILL, "scripts", "apply_theme.js"));
    await applyTheme(out, THEME);
  }
  console.log("✓", path.relative(V2, out));
}

module.exports = { createDeck, save, THEME, NAVY, SLATE, SLATE2, GREY, LIGHT, AMBER, CREAM, CREAM2, INDIGO_TINT, WHITE, GREEN, BLUE, PURPLE, CODE_GREEN };
