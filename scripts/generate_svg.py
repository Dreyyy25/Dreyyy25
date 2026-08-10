"""Render `andrey.py` as a floating VS Code window, themed Tokyo Night.

The window has four regions, matching the real editor: title bar, tab bar, the
editor pane, and a docked terminal panel showing live contribution stats, with a
status bar underneath.

Two constraints shape almost every decision in here:

1. GitHub does not load web fonts in README SVGs, so text renders in whatever
   monospace the viewer happens to have. Character advance widths therefore vary
   between machines. Nothing may depend on a character grid: code lines are one
   <text> per line with flowing <tspan> children (no per-span x), and all chrome
   is drawn as shapes at fixed coordinates.
2. Decorative Unicode (block elements, box drawing, emoji) renders as tofu on
   machines missing the glyph. Every mark that isn't a letter or digit is drawn.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from fetch_stats import compute_streaks, fetch_all_history
from generate_grid import render_grid

# --- Tokyo Night palette ---------------------------------------------------
BG = "#1a1b26"          # editor background
CHROME = "#16161e"      # title / tab / terminal / status bars
FG = "#c0caf5"          # default text
STRING = "#9ece6a"      # docstrings and string literals
COMMENT = "#565f89"     # comments, gutter numbers, muted chrome
CONST = "#7aa2f7"       # module-level constant names
PUNCT = "#ff9e64"       # brackets, operators
CYAN = "#7dcfff"        # terminal prompt, filled meter
RED = "#f7768e"
AMBER = "#e0af68"

# --- Geometry --------------------------------------------------------------
PAD = 20                # canvas inset, so the drop shadow is not clipped
WIN_X = PAD
WIN_Y = PAD
WIN_W = 820

TITLE_H = 34
TAB_H = 32
GUTTER_W = 52
LINE_H = 21
CODE_PAD_Y = 12
N_LINES = 16
EDITOR_H = CODE_PAD_Y * 2 + N_LINES * LINE_H

TERM_HEADER_H = 26
TERM_LINE_H = 19
TERM_LINES = 3
TERM_H = TERM_HEADER_H + 12 + TERM_LINES * TERM_LINE_H + 12

STATUS_H = 24

WIN_H = TITLE_H + TAB_H + EDITOR_H + TERM_H + STATUS_H
CANVAS_W = WIN_W + PAD * 2
CANVAS_H = WIN_H + PAD * 2

TITLE_Y = WIN_Y
TAB_Y = TITLE_Y + TITLE_H
EDITOR_Y = TAB_Y + TAB_H
TERM_Y = EDITOR_Y + EDITOR_H
STATUS_Y = TERM_Y + TERM_H

CODE_X = WIN_X + GUTTER_W + 16
GUTTER_NUM_X = WIN_X + GUTTER_W - 12

MONO = ("'JetBrains Mono','Fira Code','SFMono-Regular',"
        "Consolas,Menlo,'DejaVu Sans Mono',monospace")

# --- File content ----------------------------------------------------------
# Each line is a list of (text, colour) spans rendered as flowing <tspan>s.
# An empty list is a blank line.
Q = '"""'

CODE: list[list[tuple[str, str]]] = [
    [(Q, STRING)],
    [("Andrey Jay Almosara — backend engineer, Metro Manila.", STRING)],
    [],
    [("I build multi-tenant SaaS backends for regulated", STRING)],
    [("industries: legal, healthcare, fintech. Schemas, auth,", STRING)],
    [("and AI agent pipelines that survive real tenants.", STRING)],
    [(Q, STRING)],
    [],
    [("SHIPPED", CONST), (" = ", FG), ("[", PUNCT)],
    [("    ", FG), ('"20+ table multi-tenant schema, zero leakage"', STRING),
     (",", PUNCT)],
    [("    ", FG), ('"HIPAA auth stack — OAuth2 + PKCE + Argon2"', STRING),
     (",", PUNCT)],
    [("    ", FG), ('"async job polling that killed API timeouts"', STRING),
     (",", PUNCT)],
    [("]", PUNCT)],
    [],
    [("STACK", CONST), (" = ", FG), ("[", PUNCT),
     ('"Python"', STRING), (", ", PUNCT),
     ('"FastAPI"', STRING), (", ", PUNCT),
     ('"Django"', STRING), (", ", PUNCT),
     ('"PostgreSQL"', STRING), ("]", PUNCT)],
    [],  # line 16 holds the cursor only
]

METER_CEILING = 2000    # commits/year that fills the meter
METER_BLOCKS = 20

# Minimap: derived from CODE, so it can never drift out of sync with the file.
MAP_W = 76
MAP_X = WIN_X + WIN_W - 92
MAP_LINE_H = 7
MAP_BAR_H = 3
MAP_SCALE = 0.9         # px of minimap per character of source


def _defs() -> str:
    return f"""  <defs>
    <clipPath id="win">
      <rect x="{WIN_X}" y="{WIN_Y}" width="{WIN_W}" height="{WIN_H}" rx="12"/>
    </clipPath>
    <filter id="shadow" x="-25%" y="-25%" width="150%" height="150%">
      <feDropShadow dx="0" dy="2" stdDeviation="3"
                    flood-color="#000000" flood-opacity="0.40"/>
      <feDropShadow dx="0" dy="14" stdDeviation="20"
                    flood-color="#000000" flood-opacity="0.45"/>
    </filter>
    <style>
      .code {{ font-family: {MONO}; font-size: 14px; }}
      .num  {{ font-family: {MONO}; font-size: 12px; fill: {COMMENT}; }}
      .tab  {{ font-family: {MONO}; font-size: 12.5px; fill: {FG}; }}
      .ttl  {{ font-family: {MONO}; font-size: 12px; fill: {COMMENT}; }}
      .term {{ font-family: {MONO}; font-size: 12.5px; }}
      .hdr  {{ font-family: {MONO}; font-size: 10.5px; fill: {COMMENT};
               letter-spacing: 1.2px; }}
      .stat {{ font-family: {MONO}; font-size: 11px; fill: {COMMENT}; }}
    </style>
  </defs>"""


def _title_bar() -> str:
    cy = TITLE_Y + TITLE_H / 2
    lights = "".join(
        f'<circle cx="{WIN_X + 18 + i * 20}" cy="{cy}" r="6" fill="{c}"/>'
        for i, c in enumerate((RED, AMBER, STRING))
    )
    # overflow affordance: three dots, drawn rather than a Unicode ellipsis
    dots = "".join(
        f'<circle cx="{WIN_X + WIN_W - 34 + i * 7}" cy="{cy}" r="1.6" '
        f'fill="{COMMENT}"/>'
        for i in range(3)
    )
    return f"""  <rect x="{WIN_X}" y="{TITLE_Y}" width="{WIN_W}" height="{TITLE_H}"
        fill="{CHROME}"/>
  {lights}
  <text x="{WIN_X + WIN_W / 2}" y="{cy + 4}" class="ttl"
        text-anchor="middle">andrey.py — Dreyyy25</text>
  {dots}"""


def _tab_bar() -> str:
    tab_w = 176
    cy = TAB_Y + TAB_H / 2
    ix = WIN_X + 16          # python mark
    tx = WIN_X + tab_w - 22  # close mark
    return f"""  <rect x="{WIN_X}" y="{TAB_Y}" width="{WIN_W}" height="{TAB_H}"
        fill="{CHROME}"/>
  <rect x="{WIN_X}" y="{TAB_Y}" width="{tab_w}" height="{TAB_H}" fill="{BG}"/>
  <rect x="{WIN_X}" y="{TAB_Y}" width="{tab_w}" height="2" fill="{CONST}"/>
  <rect x="{ix}" y="{cy - 6}" width="6" height="9" rx="2" fill="#4584b6"/>
  <rect x="{ix + 4}" y="{cy - 3}" width="6" height="9" rx="2" fill="#ffde57"/>
  <text x="{ix + 20}" y="{cy + 4}" class="tab">andrey.py</text>
  <path d="M{tx} {cy - 3.5} l7 7 M{tx + 7} {cy - 3.5} l-7 7"
        stroke="{COMMENT}" stroke-width="1.3" stroke-linecap="round"/>"""


def _minimap() -> str:
    """The condensed file preview VS Code docks on the right edge."""
    top = EDITOR_Y + CODE_PAD_Y + 4
    out = [
        f'  <rect x="{MAP_X - 6}" y="{top - 5}" width="{MAP_W + 12}" '
        f'height="{len(CODE) * MAP_LINE_H + 6}" fill="#ffffff" '
        f'opacity="0.035" rx="2"/>'
    ]
    for i, spans in enumerate(CODE):
        x = MAP_X
        y = top + i * MAP_LINE_H
        for text, colour in spans:
            w = len(text) * MAP_SCALE
            if x + w > MAP_X + MAP_W:        # clamp at the minimap edge
                w = max(0.0, MAP_X + MAP_W - x)
            if text.strip() and w > 0:
                out.append(
                    f'  <rect x="{x:.1f}" y="{y}" width="{w:.1f}" '
                    f'height="{MAP_BAR_H}" rx="1" fill="{colour}" '
                    f'opacity="0.5"/>'
                )
            x += w
            if x >= MAP_X + MAP_W:
                break
    return "\n".join(out)


def _editor() -> str:
    out = [
        f'  <rect x="{WIN_X}" y="{EDITOR_Y}" width="{WIN_W}" '
        f'height="{EDITOR_H}" fill="{BG}"/>'
    ]
    for i in range(N_LINES):
        base = EDITOR_Y + CODE_PAD_Y + i * LINE_H + 15
        out.append(
            f'  <text x="{GUTTER_NUM_X}" y="{base}" class="num" '
            f'text-anchor="end">{i + 1}</text>'
        )
        spans = CODE[i]
        if not spans:
            continue
        tspans = "".join(
            f'<tspan fill="{colour}">{escape(text)}</tspan>'
            for text, colour in spans
        )
        out.append(
            f'  <text x="{CODE_X}" y="{base}" class="code" '
            f'xml:space="preserve">{tspans}</text>'
        )

    # Block cursor on the last line. A <rect>, not a block-element glyph.
    cur_y = EDITOR_Y + CODE_PAD_Y + (N_LINES - 1) * LINE_H + 2
    out.append(
        f'  <rect x="{CODE_X}" y="{cur_y}" width="2" height="17" fill="{FG}">'
        f'<animate attributeName="opacity" values="1;1;0;0" dur="1.06s" '
        f'repeatCount="indefinite"/></rect>'
    )
    out.append(_minimap())
    return "\n".join(out)


def _meter(x: float, y: float, ratio: float) -> str:
    bw, gap = 9, 3
    filled = round(ratio * METER_BLOCKS)
    blocks = []
    for i in range(METER_BLOCKS):
        on = i < filled
        fill = CYAN if on else COMMENT
        dim = "" if on else ' opacity="0.3"'
        blocks.append(
            f'<rect x="{x + i * (bw + gap)}" y="{y}" width="{bw}" height="8" '
            f'rx="1.5" fill="{fill}"{dim}/>'
        )
    return "".join(blocks)


def _terminal(total: int, current: int, longest: int) -> str:
    cy = TERM_Y + TERM_HEADER_H / 2
    x = WIN_X + WIN_W - 46
    body = TERM_Y + TERM_HEADER_H + 12

    def base(i: int) -> float:
        return body + i * TERM_LINE_H + 14

    ratio = min(max(total / METER_CEILING, 0.0), 1.0)
    label_x = CODE_X + 16
    val_x = CODE_X + 210
    return f"""  <rect x="{WIN_X}" y="{TERM_Y}" width="{WIN_W}" height="{TERM_H}"
        fill="{CHROME}"/>
  <line x1="{WIN_X}" y1="{TERM_Y}" x2="{WIN_X + WIN_W}" y2="{TERM_Y}"
        stroke="{COMMENT}" stroke-opacity="0.25"/>
  <text x="{CODE_X}" y="{cy + 4}" class="hdr">TERMINAL</text>
  <rect x="{CODE_X}" y="{TERM_Y + TERM_HEADER_H - 3}" width="66"
        height="2" fill="{CONST}"/>
  <path d="M{x} {cy + 2} l4 -4 l4 4" stroke="{COMMENT}" stroke-width="1.3"
        fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M{x + 18} {cy - 3.5} l7 7 M{x + 25} {cy - 3.5} l-7 7"
        stroke="{COMMENT}" stroke-width="1.3" stroke-linecap="round"/>

  <text x="{CODE_X}" y="{base(0)}" class="term" xml:space="preserve"><tspan
        fill="{CYAN}">$ </tspan><tspan fill="{FG}">gh stats --user \
Dreyyy25</tspan></text>

  <text x="{label_x}" y="{base(1)}" class="term"
        fill="{COMMENT}">commits (12mo)</text>
  <text x="{val_x}" y="{base(1)}" class="term" text-anchor="end"
        fill="{FG}">{total:,}</text>
  {_meter(val_x + 22, base(1) - 8, ratio)}

  <text x="{label_x}" y="{base(2)}" class="term"
        fill="{COMMENT}">current streak</text>
  <text x="{val_x}" y="{base(2)}" class="term" text-anchor="end"
        fill="{FG}">{current}</text>
  <text x="{val_x + 6}" y="{base(2)}" class="term" fill="{COMMENT}">d</text>
  <text x="{val_x + 76}" y="{base(2)}" class="term"
        fill="{COMMENT}">longest</text>
  <text x="{val_x + 190}" y="{base(2)}" class="term" text-anchor="end"
        fill="{FG}">{longest}</text>
  <text x="{val_x + 196}" y="{base(2)}" class="term" fill="{COMMENT}">d</text>"""


def _status_bar() -> str:
    cy = STATUS_Y + STATUS_H / 2
    b = WIN_X + 16                       # git branch mark
    d = WIN_X + WIN_W - 132              # open-to-work diamond
    return f"""  <rect x="{WIN_X}" y="{STATUS_Y}" width="{WIN_W}"
        height="{STATUS_H}" fill="{CHROME}"/>
  <line x1="{WIN_X}" y1="{STATUS_Y}" x2="{WIN_X + WIN_W}" y2="{STATUS_Y}"
        stroke="{COMMENT}" stroke-opacity="0.25"/>
  <g stroke="{COMMENT}" fill="none" stroke-width="1.2">
    <circle cx="{b}" cy="{cy - 4}" r="2"/>
    <circle cx="{b}" cy="{cy + 4}" r="2"/>
    <circle cx="{b + 9}" cy="{cy - 4}" r="2"/>
    <path d="M{b} {cy - 2} v4 M{b + 9} {cy - 2} q0 4 -9 4"/>
  </g>
  <text x="{b + 18}" y="{cy + 4}" class="stat">main*</text>
  <text x="{b + 74}" y="{cy + 4}" class="stat">Python 3.12</text>
  <text x="{b + 172}" y="{cy + 4}" class="stat">UTF-8</text>
  <text x="{b + 232}" y="{cy + 4}" class="stat">Ln 16, Col 1</text>
  <path d="M{d} {cy} l4 -4 l4 4 l-4 4 z" fill="{STRING}"/>
  <text x="{d + 14}" y="{cy + 4}" class="stat"
        fill="{STRING}">open to work</text>"""


def render_svg(total: int, current: int, longest: int) -> str:
    """Build the SVG. Pure: no network, no environment reads."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" \
height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img"
     aria-label="andrey.py open in a code editor: Andrey Jay Almosara, \
backend engineer, Metro Manila">
{_defs()}
  <rect x="{WIN_X}" y="{WIN_Y}" width="{WIN_W}" height="{WIN_H}" rx="12"
        fill="{BG}" filter="url(#shadow)"/>
  <g clip-path="url(#win)">
{_title_bar()}
{_tab_bar()}
{_editor()}
{_terminal(total, current, longest)}
{_status_bar()}
  </g>
  <rect x="{WIN_X}" y="{WIN_Y}" width="{WIN_W}" height="{WIN_H}" rx="12"
        fill="none" stroke="{COMMENT}" stroke-opacity="0.3"/>
</svg>
"""


def render(window_path: Path, grid_path: Path) -> None:
    """Fetch once, render both SVGs.

    fetch_all_history pages the GraphQL API a year at a time, so it is the
    expensive part; the grid and the window share a single call.
    """
    token = os.environ["GH_TOKEN"]
    login = os.environ.get("GH_LOGIN", "Dreyyy25")

    days, total = fetch_all_history(token, login)
    current, longest = compute_streaks(days)

    window_path.write_text(render_svg(total, current, longest),
                           encoding="utf-8")
    grid_path.write_text(render_grid(days, total), encoding="utf-8")
    print(f"wrote {window_path} and {grid_path} - total={total} "
          f"current={current} longest={longest}")


def _sample() -> None:
    """Render both SVGs from synthetic data, for eyeballing without a token."""
    import random
    from datetime import date, timedelta

    rng = random.Random(7)
    today = date.today()
    days = []
    for i in range(400):
        d = today - timedelta(days=i)
        # Weekday-weighted, with quiet stretches, so the ramp gets exercised.
        base = 0 if rng.random() < 0.28 else rng.randint(1, 9)
        if d.weekday() >= 5:
            base = base // 2
        days.append((d, base))
    days.reverse()

    Path("profile.svg").write_text(render_svg(1081, 1, 12), encoding="utf-8")
    Path("contributions.svg").write_text(
        render_grid(days, sum(c for _, c in days)), encoding="utf-8")
    print("wrote profile.svg and contributions.svg (sample data)")


if __name__ == "__main__":
    if "--sample" in sys.argv:
        _sample()
    else:
        render(Path("profile.svg"), Path("contributions.svg"))
