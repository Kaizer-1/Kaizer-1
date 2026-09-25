"""Builds the profile README and every SVG it uses.

    pip install -r readme-src/requirements.txt
    python readme-src/build.py

Edit the CONTENT section, run it, commit README.md and assets/. Fonts (all OFL)
are downloaded from the Google Fonts repo on first run.
"""
import json, urllib.request
from pathlib import Path
from typeset import Face, SVG, balanced, para

# ============================================================== CONTENT
USER = "Kaizer-1"
NAME_TEXT = "Kaizer Dewaswala"
THESIS = ("Most of what I build sits around the model rather than inside it: routing "
          "each question to the right source, spending compute only where it pays off, "
          "and checking answers before anyone relies on them.")
FACTS = ("AI systems engineer in the final year of Information Science at RV College "
         "of Engineering, Bengaluru. Currently a software intern at Galaxy Weblinks.")
RESULTS_INTRO = "Four things I made faster or cheaper. Pale is where each started, solid is where it ended up."
# slug, name, caption, value, note, after as a fraction of before, low end of a before-range, link
ROWS = [
    ("company-brain", "Company Brain", "Knowledge ingestion", "6 s", "was 52 s", 6 / 52, None,
     "https://github.com/Kaizer-1/Company-Brain"),
    ("respondr", "Respondr", "Emergency call triage", "under 30 s", "was 2–3 min", 30 / 180, 120 / 180,
     "https://github.com/Kaizer-1/Respondr"),
    ("llm-council", "LLM Council", "Cost of multi-agent debate", "42%", "of the cost, at 94% of the quality", .42, None,
     "https://github.com/Kaizer-1/LLM-Council"),
    ("galaxy", "Galaxy Weblinks", "Reviewing agent output", "65%", "of the manual review, roughly", .65, None, None),
]
TOOLS = ("Python first, then JavaScript, C++ and SQL. LangGraph, LangChain and MCP for "
         "agents; FastAPI, Node and Express for services; Postgres and Neo4j for data; "
         "React and Next.js for interfaces; an ESP32 when the problem needs hardware.")
EMAIL = "dewaswalakaizer@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/kaizer-dewaswala"

# ============================================================== SYSTEM
ROOT = Path(__file__).resolve().parent.parent
FONTS, OUT = ROOT / "readme-src" / "fonts", ROOT / "assets"
BASE = f"https://raw.githubusercontent.com/{USER}/{USER}/main/assets"
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
FONT_FILES = {"Newsreader[opsz,wght].ttf": "newsreader/Newsreader%5Bopsz,wght%5D.ttf",
              "SchibstedGrotesk[wght].ttf": "schibstedgrotesk/SchibstedGrotesk%5Bwght%5D.ttf"}
FONTS.mkdir(parents=True, exist_ok=True); OUT.mkdir(exist_ok=True)
for f, url in FONT_FILES.items():
    if not (FONTS / f).exists():
        urllib.request.urlretrieve(GF + url, FONTS / f)

NAME  = Face(str(FONTS / "Newsreader[opsz,wght].ttf"), {"opsz": 72, "wght": 300})
VALUE = Face(str(FONTS / "Newsreader[opsz,wght].ttf"), {"opsz": 26, "wght": 340})
LABEL = Face(str(FONTS / "Newsreader[opsz,wght].ttf"), {"opsz": 24, "wght": 360})
TEXT  = Face(str(FONTS / "SchibstedGrotesk[wght].ttf"), {"wght": 400})
TEXTM = Face(str(FONTS / "SchibstedGrotesk[wght].ttf"), {"wght": 520})
NUMF = {"kern": True, "liga": True, "lnum": True}

W, COL, MEASURE = 880, 236, 568   # canvas, content column, line length
THEMES = {
    "dark":  dict(ink="#ffffff", name=.95, strong=.92, body=.68, muted=.47, ghost=.14, ghost2=.07, line=.32),
    "light": dict(ink="#000000", name=.92, strong=.88, body=.70, muted=.52, ghost=.10, ghost2=.05, line=.30),
}

def save(slug, theme, svg): (OUT / f"{slug}-{theme}.svg").write_text(svg.render())
def section(s, T, label, y): s.text(LABEL, label, 0, y + 1, 22, T["ink"], T["strong"])

def header(t, T):
    s = SVG(W, 400, NAME_TEXT)
    s.text(NAME, NAME_TEXT, -3, 94, 98, T["ink"], T["name"], tracking=-0.018)
    y = 164
    for ln in balanced(s, TEXT, THESIS, 20, MEASURE):
        s.text(TEXT, ln, COL, y, 20, T["ink"], T["body"]); y += 31
    y += 12
    for ln in para(s, TEXT, FACTS, 15, MEASURE):
        s.text(TEXT, ln, COL, y, 15, T["ink"], T["muted"]); y += 23
    y += 62
    section(s, T, "Results", y)
    for ln in para(s, TEXT, RESULTS_INTRO, 15, MEASURE):
        s.text(TEXT, ln, COL, y, 15, T["ink"], T["muted"]); y += 23
    s.h = int(y + 6); save("header", t, s)

BAR_X, BAR_W, BAR_Y, BAR_H, VAL_X = COL, 352, 13, 6, 620
def row(t, T, i, r):
    slug, name, cap, val, note, ratio, rng, _ = r
    s = SVG(W, 66, f"{name}: {val}, {note}")
    s.text(TEXTM, name, 0, 24, 16, T["ink"], T["strong"])
    s.text(TEXT, cap, 0, 46, 14, T["ink"], T["muted"])
    if rng:   # a range for the starting point: firm up to its low end, fainter to its high end
        s.raw(f'<rect x="{BAR_X}" y="{BAR_Y}" width="{BAR_W*rng:.1f}" height="{BAR_H}" fill="{T["ink"]}" opacity="{T["ghost"]}"/>')
        s.raw(f'<rect x="{BAR_X+BAR_W*rng:.1f}" y="{BAR_Y}" width="{BAR_W*(1-rng):.1f}" height="{BAR_H}" fill="{T["ink"]}" opacity="{T["ghost2"]}"/>')
    else:
        s.raw(f'<rect x="{BAR_X}" y="{BAR_Y}" width="{BAR_W}" height="{BAR_H}" fill="{T["ink"]}" opacity="{T["ghost"]}"/>')
    s.raw(f'<rect class="a" x="{BAR_X}" y="{BAR_Y}" width="{BAR_W*ratio:.1f}" height="{BAR_H}" fill="{T["ink"]}" opacity="{T["strong"]}"/>')
    # the one moment of motion: each solid bar starts at its "before" length and settles on "after"
    s.style.append(f".a{{transform-origin:{BAR_X}px 0;animation:k 1.7s cubic-bezier(.16,1,.3,1) {.45 + .14*i:.2f}s both}}"
                   f"@keyframes k{{from{{transform:scaleX({1/ratio:.4f})}}}}"
                   "@media (prefers-reduced-motion:reduce){.a{animation:none}}")
    s.text(VALUE, val, VAL_X, 25, 26, T["ink"], T["name"], features=NUMF)
    s.text(TEXT, note, VAL_X, 46, 14, T["ink"], T["muted"], features=NUMF)
    save(f"row-{slug}", t, s)

def tools(t, T):
    s = SVG(W, 150, "Tools"); y = top = 64
    section(s, T, "Tools", top)
    for ln in para(s, TEXT, TOOLS, 17, MEASURE):
        s.text(TEXT, ln, COL, y, 17, T["ink"], T["body"]); y += 27
    s.h = int(y + 6); save("tools", t, s)

CH, CB = 58, 40
def contact(t, T):
    s = SVG(COL, CH, "Contact"); section(s, T, "Contact", CB); save("contact", t, s)
    widths = {"contact": COL}
    for slug, label in (("email", EMAIL), ("linkedin", "LinkedIn")):
        w = TEXT.width(label, 17); box = round(w + 36)
        s = SVG(box, CH, label)
        s.text(TEXT, label, 0, CB, 17, T["ink"], T["strong"])
        s.raw(f'<rect x="0" y="{CB+5}" width="{w:.1f}" height="1" fill="{T["ink"]}" opacity="{T["line"]}"/>')
        save(slug, t, s); widths[slug] = box
    return widths

for t, T in THEMES.items():
    header(t, T)
    for i, r in enumerate(ROWS): row(t, T, i, r)
    tools(t, T)
    widths = contact(t, T)

# ============================================================== README
def pic(slug, alt, units=W):
    pct = round(units / W * 100, 2)
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{BASE}/{slug}-dark.svg">'
            f'<source media="(prefers-color-scheme: light)" srcset="{BASE}/{slug}-light.svg">'
            f'<img alt="{alt}" src="{BASE}/{slug}-light.svg" width="{"100%" if pct >= 100 else f"{pct}%"}"></picture>')
def link(href, inner): return f'<a href="{href}">{inner}</a>'

lines = ["<!-- Typeset as SVG so it looks the same on every machine. Edit readme-src/build.py and run it to regenerate. -->",
         "", "<p>", pic("header", f"{NAME_TEXT}. {THESIS} {FACTS}") + "<br>"]
for slug, name, cap, val, note, *_rest, href in ROWS:
    p = pic(f"row-{slug}", f"{name}, {cap.lower()}: {val}, {note}")
    lines.append((link(href, p) if href else p) + "<br>")
lines.append(pic("tools", f"Tools: {TOOLS}") + "<br>")
lines.append(pic("contact", "Contact", widths["contact"])
             + link(f"mailto:{EMAIL}", pic("email", EMAIL, widths["email"]))
             + link(LINKEDIN, pic("linkedin", "LinkedIn", widths["linkedin"])))
lines.append("</p>")
(ROOT / "README.md").write_text("\n".join(lines) + "\n")
print("wrote README.md and", len(list(OUT.glob("*.svg"))), "SVGs")
