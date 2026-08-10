"""Render the full toolchain as a themed panel of logos with a shimmer sweep.

Every tool listed in the resume's skills section that has a Simple Icons glyph,
grouped the way the work actually divides. Icons are drawn in Tokyo Night
accents rather than brand colours: two dozen brand palettes side by side fight
each other and fight the rest of the profile, whereas one accent per group
makes the grouping itself readable at a glance.

The sweep is the same trick as the contribution grid's crush wave — one shared
cycle, per-element keyTimes derived from x position, so a highlight travels
left to right. SMIL only: GitHub serves README images through <img>, where no
script runs and nothing is hoverable.
"""
from __future__ import annotations

from xml.sax.saxutils import escape

from logo_paths import LOGOS

# --- Palette ---------------------------------------------------------------
BACKDROP_HI = "#171823"
BACKDROP_LO = "#101018"
BORDER = "#565f89"
MUTED = "#565f89"
FG = "#c0caf5"
AURORA_A = "#7aa2f7"
AURORA_B = "#bb9af7"

BLUE = "#7aa2f7"
GREEN = "#9ece6a"
CYAN = "#7dcfff"
PURPLE = "#bb9af7"
AMBER = "#e0af68"

MONO = ("'JetBrains Mono','Fira Code','SFMono-Regular',"
        "Consolas,Menlo,'DejaVu Sans Mono',monospace")

# --- Content ---------------------------------------------------------------
GROUPS: list[tuple[str, str, list[str]]] = [
    ("languages", BLUE,
     ["python", "typescript", "javascript", "openjdk"]),
    ("backend", GREEN,
     ["fastapi", "django", "nodedotjs"]),
    ("data & auth", CYAN,
     ["postgresql", "mysql", "supabase", "firebase", "jsonwebtokens"]),
    ("ai", PURPLE,
     ["langchain", "pydantic", "googlegemini", "tensorflow", "claude",
      "openai"]),
    ("infra & web", AMBER,
     ["docker", "git", "githubactions", "amazonwebservices", "react",
      "nextdotjs"]),
]

# --- Geometry --------------------------------------------------------------
CANVAS_W = 908            # matches the other two SVGs so all three scale alike
ICON = 34
PITCH = 88
LABEL_W = 130
GAP = 30

WIDEST = max(len(s) for _, _, s in GROUPS)
ICONS_W = (WIDEST - 1) * PITCH + ICON
UNIT_W = LABEL_W + GAP + ICONS_W
LEFT = (CANVAS_W - UNIT_W) // 2
LABEL_RIGHT = LEFT + LABEL_W
ICON_X0 = LABEL_RIGHT + GAP + ICON // 2

ROW_H = 54
ROW_Y0 = 84
CANVAS_H = ROW_Y0 + (len(GROUPS) - 1) * ROW_H + ICON // 2 + 34

X_MIN = ICON_X0 - ICON / 2
X_MAX = ICON_X0 + (WIDEST - 1) * PITCH + ICON / 2

# --- Shimmer sweep ---------------------------------------------------------
CYCLE = "6s"
STEP = 0.045          # fraction of the cycle the highlight dwells on an icon
LEAD = 0.04
SPAN = 0.72
DIM = 0.62            # resting opacity
BUMP = 1.14           # scale at the peak of the sweep

SCALE = ICON / 24     # Simple Icons paths are drawn on a 24x24 grid


def _icon(slug: str, cx: float, cy: float, colour: str) -> str:
    title, d = LOGOS[slug]
    f = LEAD + ((cx - X_MIN) / (X_MAX - X_MIN)) * SPAN
    key_times = f"0;{f:.4f};{f + STEP:.4f};{f + 2 * STEP:.4f};1"
    peak = SCALE * BUMP
    return (
        f'  <g transform="translate({cx},{cy})"><g>'
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="{SCALE:.4f};{SCALE:.4f};{peak:.4f};{SCALE:.4f};{SCALE:.4f}" '
        f'keyTimes="{key_times}" dur="{CYCLE}" repeatCount="indefinite"/>'
        f'<g transform="translate(-12,-12)">'
        f'<title>{escape(title)}</title>'
        f'<path d="{d}" fill="{colour}" opacity="{DIM}">'
        f'<animate attributeName="opacity" '
        f'values="{DIM};{DIM};1;{DIM};{DIM}" keyTimes="{key_times}" '
        f'dur="{CYCLE}" repeatCount="indefinite"/></path>'
        f'</g></g></g>'
    )


def _row(index: int, label: str, colour: str, slugs: list[str]) -> str:
    cy = ROW_Y0 + index * ROW_H
    out = [
        f'  <text x="{LABEL_RIGHT}" y="{cy + 4}" class="grp" '
        f'text-anchor="end">{escape(label)}</text>'
    ]
    out += [
        _icon(slug, ICON_X0 + i * PITCH, cy, colour)
        for i, slug in enumerate(slugs)
    ]
    return "\n".join(out)


def render_stack() -> str:
    """Build the stack SVG. Pure: no network, no environment reads."""
    total = sum(len(s) for _, _, s in GROUPS)
    names = ", ".join(
        LOGOS[s][0] for _, _, slugs in GROUPS for s in slugs
    )
    rows = "\n".join(
        _row(i, label, colour, slugs)
        for i, (label, colour, slugs) in enumerate(GROUPS)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" \
height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img"
     aria-label="Toolchain: {escape(names)}">
  <defs>
    <clipPath id="sback">
      <rect x="0" y="0" width="{CANVAS_W}" height="{CANVAS_H}" rx="12"/>
    </clipPath>
    <linearGradient id="sbackdrop" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{BACKDROP_HI}"/>
      <stop offset="100%" stop-color="{BACKDROP_LO}"/>
    </linearGradient>
    <radialGradient id="sauroraA">
      <stop offset="0%" stop-color="{AURORA_A}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{AURORA_A}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="sauroraB">
      <stop offset="0%" stop-color="{AURORA_B}" stop-opacity="0.20"/>
      <stop offset="100%" stop-color="{AURORA_B}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="sdots" width="16" height="16" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="1.1" fill="{FG}" opacity="0.045"/>
    </pattern>
    <style>
      .hdr {{ font-family: {MONO}; font-size: 11.5px; fill: {MUTED}; }}
      .grp {{ font-family: {MONO}; font-size: 11px; fill: {MUTED}; }}
    </style>
  </defs>
  <rect x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{CANVAS_H - 1}" rx="12"
        fill="url(#sbackdrop)" stroke="{BORDER}" stroke-opacity="0.3"/>
  <g clip-path="url(#sback)">
    <ellipse cx="70" cy="10" rx="320" ry="170" fill="url(#sauroraA)"/>
    <ellipse cx="{CANVAS_W - 70}" cy="{CANVAS_H}" rx="330" ry="180"
             fill="url(#sauroraB)"/>
    <rect x="0" y="0" width="{CANVAS_W}" height="{CANVAS_H}" fill="url(#sdots)"/>
  </g>
  <text x="{LEFT}" y="38" class="hdr">~/stack</text>
  <text x="{X_MAX}" y="38" class="hdr" text-anchor="end">{total} tools</text>
  <line x1="{LEFT}" y1="50" x2="{X_MAX}" y2="50" stroke="{MUTED}"
        stroke-opacity="0.2"/>
{rows}
</svg>
"""
