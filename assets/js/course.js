/* Actoryx × MGIT course runtime.
   Plain JS, no build step, works from file:// so lab machines can open pages offline. */
(function () {
  "use strict";

  var PROGRAM_KEY = "ax-mgit";

  /* ---------- storage (never trusted to exist) ---------- */
  var store = {
    get: function (k, fallback) {
      try { var v = localStorage.getItem(PROGRAM_KEY + ":" + k); return v === null ? fallback : JSON.parse(v); }
      catch (e) { return fallback; }
    },
    set: function (k, v) {
      try { localStorage.setItem(PROGRAM_KEY + ":" + k, JSON.stringify(v)); } catch (e) { /* private mode */ }
    }
  };

  function doneList() { return store.get("done", []); }
  function isDone(id) { return doneList().indexOf(id) !== -1; }
  function setDone(id, on) {
    var list = doneList().filter(function (x) { return x !== id; });
    if (on) list.push(id);
    store.set("done", list);
  }

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function el(tag, attrs, html) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === "class") n.className = attrs[k]; else n.setAttribute(k, attrs[k]);
    });
    if (html !== undefined) n.innerHTML = html;
    return n;
  }
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function shuffle(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  function readJSON(root) {
    var s = $('script[type="application/json"]', root);
    try { return s ? JSON.parse(s.textContent) : null; } catch (e) { console.error("Bad JSON in", root, e); return null; }
  }

  /* ---------- theme ---------- */
  function initTheme() {
    var saved = store.get("theme", null);
    if (saved) document.documentElement.setAttribute("data-theme", saved);
    $all("[data-theme-toggle]").forEach(function (b) {
      b.addEventListener("click", function () {
        var cur = document.documentElement.getAttribute("data-theme") ||
          (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
        var next = cur === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", next);
        store.set("theme", next);
      });
    });
  }

  /* ---------- program home ---------- */
  function initHome() {
    var host = $("#journey");
    if (!host || !window.PROGRAM) return;
    var P = window.PROGRAM;
    var total = P.chapters.length;
    // trainer view (index.html?view=trainer) shows authoring status from chapters.js
    var trainer = /[?&]view=trainer\b/.test(location.search);
    var SOURCE = { ready: "Content ready", adapt: "Adapt existing", build: "Build new" };
    var STAGE = { "not-started": "Not started", drafting: "Drafting", review: "In review", published: "Published" };
    document.body.classList.toggle("trainer-view", trainer);
    function published(c) { return c.stage === "published"; }

    function render() {
      host.innerHTML = "";
      P.weeks.forEach(function (w) {
        var chs = P.chapters.filter(function (c) { return c.week === w.n; });
        if (!chs.length) return;
        host.appendChild(el("div", { class: "week-title" }, esc(w.title)));
        var grid = el("div", { class: "journey" });
        chs.forEach(function (c) {
          var idx = P.chapters.indexOf(c) + 1;
          var done = isDone(c.id);
          var locked = !published(c) && !trainer;
          var label = c.id === "lab" ? "LAB" : "CHAPTER " + String(idx).padStart(2, "0");
          var statusHtml = done ? '<span class="status done">Completed</span>'
            : !published(c) ? '<span class="status draft">' + (trainer ? "Not published" : "Coming soon") + "</span>"
            : '<span class="status available">Available</span>';
          var openText = trainer && !published(c) ? "Preview →" : "Open chapter →";
          var card = el("article", { class: "card chapter-card" + (locked ? " locked" : "") + (done ? " is-done" : "") },
            '<div class="num">' + label + "</div>" +
            "<h3>" + esc(c.title) + "</h3>" +
            (c.gita ? '<div class="gita">' + esc(c.gita) + "</div>" : "") +
            "<p>" + esc(c.summary) + "</p>" +
            (c.lessons ? '<div class="counts">📘 ' + c.lessons + " lessons · 💻 " + c.programs + " programs · 🛠️ task</div>" : "") +
            (trainer ? '<div class="build-row"><span class="pill src-' + c.source + '">' + SOURCE[c.source] + '</span>' +
              '<span class="pill stage-' + c.stage + '">' + STAGE[c.stage] + "</span></div>" : "") +
            '<div class="foot">' + statusHtml +
            '<a class="open" href="chapters/' + c.id + '/index.html"' + (locked ? ' aria-disabled="true" tabindex="-1"' : "") + ">" + openText + "</a></div>");
          grid.appendChild(card);
        });
        host.appendChild(grid);
      });
      var n = P.chapters.filter(function (c) { return isDone(c.id); }).length;
      var bar = $("#progress-bar"), lab = $("#progress-label");
      if (bar) bar.style.width = (100 * n / total) + "%";
      if (lab) lab.textContent = n + " / " + total + " chapters complete";
      var start = $("#start-link");
      if (start) {
        var next = P.chapters.filter(function (c) { return published(c) && !isDone(c.id); })[0];
        if (next) { start.href = "chapters/" + next.id + "/index.html"; start.removeAttribute("aria-disabled"); }
      }
    }
    render();
    renderStatus();
    var reset = $("#reset-progress");
    if (reset) reset.addEventListener("click", function () {
      if (confirm("Reset your progress for all chapters?")) { store.set("done", []); render(); }
    });
  }

  /* trainer view: summary of where the program stands */
  function renderStatus() {
    var host = $("#build-status");
    if (!host || !document.body.classList.contains("trainer-view")) return;
    var chs = window.PROGRAM.chapters;
    function count(key, val) { return chs.filter(function (c) { return c[key] === val; }).length; }
    host.hidden = false;
    host.innerHTML =
      "<h2>Build status</h2>" +
      '<p class="muted">Trainer view — generated from <code>assets/js/chapters.js</code>. Details, owners and gaps live in <code>STATUS.md</code>.</p>' +
      '<div class="stat-grid">' +
      '<div><b>' + count("stage", "published") + " / " + chs.length + "</b>Published</div>" +
      '<div><b>' + (count("stage", "drafting") + count("stage", "review")) + "</b>In progress</div>" +
      '<div><b class="src-ready">' + count("source", "ready") + "</b>Content ready</div>" +
      '<div><b class="src-adapt">' + count("source", "adapt") + "</b>Adapt existing</div>" +
      '<div><b class="src-build">' + count("source", "build") + "</b>Build new</div>" +
      "</div>";
  }

  /* ---------- python highlighter (small, good enough for teaching code) ---------- */
  var KW = "False None True and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield match case".split(" ");
  var BI = "print len range int float str list dict set tuple abs round min max sum sorted enumerate zip open map filter isinstance type super self np pd plt".split(" ");
  function highlightPython(src) {
    var re = /(#[^\n]*)|([rbfuRBFU]{0,2}"""[\s\S]*?"""|[rbfuRBFU]{0,2}'''[\s\S]*?'''|[rbfuRBFU]{0,2}"(?:\\.|[^"\\\n])*"|[rbfuRBFU]{0,2}'(?:\\.|[^'\\\n])*')|(\b\d+(?:\.\d+)?(?:e[+-]?\d+)?j?\b)|([A-Za-z_]\w*)(\s*\()?/g;
    var out = "", last = 0, m;
    while ((m = re.exec(src))) {
      out += esc(src.slice(last, m.index));
      if (m[1]) out += '<span class="tok-com">' + esc(m[1]) + "</span>";
      else if (m[2]) out += '<span class="tok-str">' + esc(m[2]) + "</span>";
      else if (m[3]) out += '<span class="tok-num">' + m[3] + "</span>";
      else if (m[4]) {
        var w = m[4], paren = m[5] || "";
        if (KW.indexOf(w) !== -1) out += '<span class="tok-kw">' + w + "</span>" + esc(paren);
        else if (BI.indexOf(w) !== -1) out += '<span class="tok-bi">' + w + "</span>" + esc(paren);
        else if (paren) out += '<span class="tok-fn">' + w + "</span>" + esc(paren);
        else out += w;
      }
      last = re.lastIndex;
    }
    return out + esc(src.slice(last));
  }
  /* ---------- javascript / jsx highlighter (same idea, for the ReactUI pages) ---------- */
  var JKW = "import export default from const let var function return if else for of in while async await try catch throw new true false null undefined typeof".split(" ");
  var JBI = "useState useEffect useContext createContext useParams useNavigate useLocation useSearchParams fetch console document window JSON Number Math Promise".split(" ");
  function highlightJS(src) {
    var re = /(\/\/[^\n]*|\/\*[\s\S]*?\*\/)|('(?:\\.|[^'\\\n])*'|"(?:\\.|[^"\\\n])*"|`(?:\\.|[^`\\])*`)|(\b\d+(?:\.\d+)?\b)|(<\/?)([A-Za-z][\w.]*)|([A-Za-z_$][\w$]*)(\s*\()?/g;
    var out = "", last = 0, m;
    while ((m = re.exec(src))) {
      out += esc(src.slice(last, m.index));
      if (m[1]) out += '<span class="tok-com">' + esc(m[1]) + "</span>";
      else if (m[2]) out += '<span class="tok-str">' + esc(m[2]) + "</span>";
      else if (m[3]) out += '<span class="tok-num">' + m[3] + "</span>";
      else if (m[5]) out += esc(m[4]) + '<span class="tok-fn">' + m[5] + "</span>";
      else if (m[6]) {
        var w = m[6], paren = m[7] || "";
        if (JKW.indexOf(w) !== -1) out += '<span class="tok-kw">' + w + "</span>" + esc(paren);
        else if (JBI.indexOf(w) !== -1) out += '<span class="tok-bi">' + w + "</span>" + esc(paren);
        else if (paren) out += '<span class="tok-fn">' + w + "</span>" + esc(paren);
        else out += w;
      }
      last = re.lastIndex;
    }
    return out + esc(src.slice(last));
  }
  function dedent(s) {
    s = s.replace(/^\n+|\s+$/g, "");
    var lines = s.split("\n");
    var ind = Math.min.apply(null, lines.filter(function (l) { return l.trim(); }).map(function (l) { return l.match(/^ */)[0].length; }));
    return lines.map(function (l) { return l.slice(ind); }).join("\n");
  }

  /* ---------- code blocks ----------
     <div class="code" data-file="code/01_x.py" data-lang="python" data-colab="https://...">
       <script type="text/x-python"> raw code, no escaping needed </script>
     </div>                                                                   */
  function initCode() {
    $all(".code").forEach(function (box) {
      var raw = $('script[type^="text/"]', box);
      var pre = $("pre", box);
      var src = raw ? dedent(raw.textContent) : (pre ? pre.textContent : "");
      var lang = box.getAttribute("data-lang") || "python";
      var file = box.getAttribute("data-file") || "";
      var name = box.getAttribute("data-name") || (file ? file.split("/").pop() : lang);
      var colab = box.getAttribute("data-colab");

      var head = el("div", { class: "code-head" },
        '<span class="dots"><i></i><i></i><i></i></span><span class="file">' + esc(name) + "</span>");
      var copy = el("button", { type: "button" }, "Copy");
      copy.addEventListener("click", function () {
        var done = function () { copy.textContent = "Copied ✓"; setTimeout(function () { copy.textContent = "Copy"; }, 1500); };
        if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(src).then(done, fallback);
        else fallback();
        function fallback() {
          var t = el("textarea"); t.value = src; document.body.appendChild(t); t.select();
          try { document.execCommand("copy"); done(); } catch (e) { /* ignore */ }
          t.remove();
        }
      });
      head.appendChild(copy);
      if (file) head.appendChild(el("a", { href: file, download: name }, "Download"));
      if (colab) head.appendChild(el("a", { href: colab, target: "_blank", rel: "noopener" }, "Open in Colab"));

      var newPre = el("pre");
      var code = el("code");
      code.innerHTML = lang === "python" ? highlightPython(src) : /^(js|jsx|javascript)$/.test(lang) ? highlightJS(src) : esc(src);
      newPre.appendChild(code);
      box.innerHTML = "";
      box.appendChild(head);
      box.appendChild(newPre);
    });
  }

  /* ---------- match the terms (click or drag) ---------- */
  function initMatch() {
    $all(".match-game").forEach(function (game) {
      var pairs = readJSON(game) || [];
      var board = el("div", { class: "match" });
      var terms = el("div", { class: "col" });
      var defs = el("div", { class: "col" });
      board.appendChild(terms); board.appendChild(defs);
      var actions = el("div", { class: "match-actions" });
      var check = el("button", { class: "btn", type: "button" }, "Check answers");
      var again = el("button", { class: "btn secondary", type: "button" }, "↺ Try again");
      var score = el("span", { class: "score" });
      actions.appendChild(check); actions.appendChild(again); actions.appendChild(score);
      game.appendChild(board); game.appendChild(actions);

      var selected = null;
      function build() {
        terms.innerHTML = ""; defs.innerHTML = ""; score.textContent = ""; selected = null;
        shuffle(pairs).forEach(function (p) {
          var t = el("button", { class: "term", type: "button", draggable: "true", "data-term": p[0] }, esc(p[0]));
          t.addEventListener("click", function () {
            $all(".term", terms).forEach(function (x) { x.classList.remove("selected"); });
            selected = t; t.classList.add("selected");
          });
          t.addEventListener("dragstart", function (e) { e.dataTransfer.setData("text/plain", p[0]); });
          terms.appendChild(t);
        });
        shuffle(pairs).forEach(function (p) {
          var d = el("button", { class: "def", type: "button", "data-answer": p[0] },
            '<span class="slot">drop here</span>' + esc(p[1]));
          d.addEventListener("click", function () { if (selected) place(d, selected.getAttribute("data-term")); });
          d.addEventListener("dragover", function (e) { e.preventDefault(); d.classList.add("over"); });
          d.addEventListener("dragleave", function () { d.classList.remove("over"); });
          d.addEventListener("drop", function (e) { e.preventDefault(); d.classList.remove("over"); place(d, e.dataTransfer.getData("text/plain")); });
          defs.appendChild(d);
        });
      }
      function place(def, term) {
        $all(".def", defs).forEach(function (d) { if (d.getAttribute("data-given") === term) { d.removeAttribute("data-given"); $(".slot", d).textContent = "drop here"; } });
        def.setAttribute("data-given", term);
        $(".slot", def).textContent = term;
        def.classList.remove("right", "wrong");
        $all(".term", terms).forEach(function (t) {
          var used = $all(".def", defs).some(function (d) { return d.getAttribute("data-given") === t.getAttribute("data-term"); });
          t.classList.toggle("used", used); t.classList.remove("selected");
        });
        selected = null;
      }
      check.addEventListener("click", function () {
        var ok = 0;
        $all(".def", defs).forEach(function (d) {
          var right = d.getAttribute("data-given") === d.getAttribute("data-answer");
          d.classList.toggle("right", right); d.classList.toggle("wrong", !right);
          if (right) ok++;
        });
        score.textContent = ok + " / " + pairs.length + " correct" + (ok === pairs.length ? " 🎉" : "");
      });
      again.addEventListener("click", build);
      build();
    });
  }

  /* ---------- knowledge test ---------- */
  function initQuiz() {
    $all(".quiz").forEach(function (quiz, qi) {
      var qs = readJSON(quiz) || [];
      var chapter = document.body.getAttribute("data-chapter") || "x";
      var list = el("div");
      qs.forEach(function (q, i) {
        var box = el("div", { class: "q", "data-answer": q.answer });
        box.appendChild(el("div", { class: "stem" }, esc(q.q)));
        q.options.forEach(function (o, j) {
          box.appendChild(el("label", null,
            '<input type="radio" name="q' + qi + "_" + i + '" value="' + j + '"><span>' + esc(o) + "</span>"));
        });
        if (q.why) box.appendChild(el("div", { class: "why" }, "💡 " + esc(q.why)));
        list.appendChild(box);
      });
      var actions = el("div", { class: "quiz-actions" });
      var check = el("button", { class: "btn primary", type: "button" }, "Submit answers");
      var reset = el("button", { class: "btn secondary", type: "button" }, "↺ Retry");
      var score = el("span", { class: "score" });
      var best = store.get("quiz:" + chapter, null);
      if (best !== null) score.textContent = "Best score: " + best + " / " + qs.length;
      actions.appendChild(check); actions.appendChild(reset); actions.appendChild(score);
      quiz.appendChild(list); quiz.appendChild(actions);

      check.addEventListener("click", function () {
        var ok = 0;
        $all(".q", list).forEach(function (box) {
          var ans = box.getAttribute("data-answer");
          var picked = $("input:checked", box);
          var right = picked && picked.value === ans;
          box.classList.add("checked");
          box.classList.toggle("right", !!right); box.classList.toggle("wrong", !right);
          $all("label", box).forEach(function (l) { l.classList.toggle("correct", $("input", l).value === ans); });
          if (right) ok++;
        });
        var prev = store.get("quiz:" + chapter, 0);
        if (ok > prev) store.set("quiz:" + chapter, ok);
        score.textContent = ok + " / " + qs.length + " correct" + (ok === qs.length ? " — perfect!" : "");
      });
      reset.addEventListener("click", function () {
        $all(".q", list).forEach(function (box) {
          box.classList.remove("checked", "right", "wrong");
          $all("label", box).forEach(function (l) { l.classList.remove("correct"); });
          $all("input", box).forEach(function (i) { i.checked = false; });
        });
        score.textContent = "";
      });
    });
  }

  /* ---------- chapter: sidebar + one lesson at a time ---------- */
  function initChapter() {
    var chapter = document.body.getAttribute("data-chapter");
    var lessons = $all(".lesson");
    var nav = $("#lesson-list");
    if (!chapter || !lessons.length || !nav) return;

    lessons.forEach(function (sec, i) {
      sec.id = sec.id || "l" + (i + 1);
      var kind = sec.getAttribute("data-kind");
      var icon = { quiz: "📝", task: "🛠️", match: "🔗", project: "🚀" }[kind] || "";
      var li = el("li");
      var b = el("button", { type: "button", "data-target": sec.id },
        '<span class="n">' + (i + 1) + ".</span><span>" + esc(sec.getAttribute("data-title") || $("h2", sec).textContent) + "</span>" +
        (icon ? '<span class="kind" aria-hidden="true">' + icon + "</span>" : ""));
      b.addEventListener("click", function () { show(i, true); });
      li.appendChild(b); nav.appendChild(li);

      var ln = el("div", { class: "lesson-nav" });
      var prev = el("button", { class: "btn secondary", type: "button" }, "← Previous");
      var next = el("button", { class: "btn", type: "button" }, "Next →");
      if (i === 0) prev.disabled = true;
      if (i === lessons.length - 1) { next.textContent = "Finish chapter ✓"; next.className = "btn primary"; }
      prev.addEventListener("click", function () { show(i - 1, true); });
      next.addEventListener("click", function () {
        if (i === lessons.length - 1) { markDone(true); window.scrollTo({ top: 0, behavior: "smooth" }); }
        else show(i + 1, true);
      });
      ln.appendChild(prev); ln.appendChild(next);
      sec.appendChild(ln);
    });

    function show(i, scroll) {
      i = Math.max(0, Math.min(lessons.length - 1, i));
      lessons.forEach(function (s, j) { s.classList.toggle("active", j === i); });
      $all("button", nav).forEach(function (b, j) { b.setAttribute("aria-current", j === i ? "true" : "false"); });
      if (history.replaceState) history.replaceState(null, "", "#" + lessons[i].id);
      store.set("pos:" + chapter, i);
      var sb = $(".sidebar"); if (sb) sb.classList.remove("open");
      if (scroll) { var top = $(".layout").getBoundingClientRect().top + window.scrollY - 70; window.scrollTo({ top: top, behavior: "smooth" }); }
    }

    var start = 0;
    var hash = location.hash.replace("#", "");
    lessons.forEach(function (s, j) { if (s.id === hash) start = j; });
    if (!hash) start = store.get("pos:" + chapter, 0);
    show(start, false);
    // a link to "#id" on the same page (e.g. Day 3's ReactUI tag) opens that step
    window.addEventListener("hashchange", function () {
      var h = location.hash.replace("#", "");
      lessons.forEach(function (sec, j) { if (sec.id === h) show(j, true); });
    });
    // the #lN hash makes the browser jump to the section; keep the chapter header in view instead
    window.addEventListener("load", function () { window.scrollTo(0, 0); });

    var toggle = $(".sidebar-toggle");
    if (toggle) toggle.addEventListener("click", function () { $(".sidebar").classList.toggle("open"); });

    var mark = $("#mark-complete");
    function markDone(on) {
      setDone(chapter, on);
      if (mark) {
        mark.textContent = on ? "Completed ✓" : "Mark complete ✓";
        mark.classList.toggle("done", on);
      }
    }
    if (mark) {
      markDone(isDone(chapter));
      mark.addEventListener("click", function () { markDone(!isDone(chapter)); });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    initHome();
    initCode();
    initMatch();
    initQuiz();
    initChapter();
  });
})();
