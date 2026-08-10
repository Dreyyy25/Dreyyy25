"""Render the toolchain as IconBar-style pills that name themselves in turn.

Adapted from the 21st.dev IconBar component (React + motion): a pill holding an
icon expands horizontally to reveal its label, and its neighbours slide over to
make room. The original expands on hover; hover is unreachable here — GitHub
serves README images through <img>, which hit-tests as one opaque box — so the
expansion runs on a timer instead, one pill at a time.

Rows animate in parallel, each cycling through its own pills, so exactly one
pill per row is open at any moment. Strictly one across the whole panel would
mean a 24-slot cycle: over half a minute before some tools were ever named.

Label widths are estimated from character count rather than measured, since
GitHub loads no web fonts and there is nothing to measure against. That only
holds because the labels are monospace — every fallback in the stack lands near
a 0.6em advance, so the estimate stays within a pixel or two.
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
PILL_BASE = "#1c1e2b"

BLUE = "#7aa2f7"
GREEN = "#9ece6a"
CYAN = "#7dcfff"
PURPLE = "#bb9af7"
AMBER = "#e0af68"

MONO = ("'JetBrains Mono','Fira Code','SFMono-Regular',"
        "Consolas,Menlo,'DejaVu Sans Mono',monospace")

# Simple Icons titles are inconsistent for display use; these read better and
# keep the widest pill narrow enough for the row to fit.
LABELS = {
    "openjdk": "Java",
    "nodedotjs": "Node.js",
    "nextdotjs": "Next.js",
    "amazonwebservices": "AWS",
    "googlegemini": "Gemini",
    "jsonwebtokens": "JWT",
    "githubactions": "Actions",
}

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

# --- Pill geometry ---------------------------------------------------------
CANVAS_W = 908            # matches the other two SVGs so all three scale alike
PILL_H = 38
ICON_CELL = 38            # square cell the icon sits in, and the collapsed width
ICON_SIZE = 20
FONT = 13
CHAR_W = FONT * 0.62      # monospace advance, the reason estimating works
PAD_R = 14
PILL_GAP = 9

LABEL_W = 118
LABEL_GAP = 26
ROW_H = 54
ROW_Y0 = 84

SCALE = ICON_SIZE / 24    # Simple Icons paths are drawn on a 24x24 grid

# --- Timing (IconBar's fluid ease, on a loop) ------------------------------
CYCLE = "9s"
EASE = "0.16 1 0.3 1"
# The label rides an ease-in instead, so it stays near zero until the pill has
# most of its width. That is what keeps the text from spilling past the pill
# mid-expansion — an animated <clipPath> would be the obvious fix, but SMIL
# inside a non-rendered container does not run reliably.
TEXT_EASE = "0.85 0 1 1"
# ...but the same curve on the way out leaves the label hanging over the
# neighbouring pill while its own shrinks away, so collapsing text drops fast.
TEXT_EASE_OUT = "0 0 0.15 1"


def _label(slug: str) -> str:
    return LABELS.get(slug, LOGOS[slug][0])


def _open_w(slug: str) -> float:
    return ICON_CELL + len(_label(slug)) * CHAR_W + PAD_R


def _blend(fg: str, bg: str, alpha: float) -> str:
    """Flatten fg over bg at alpha — SMIL cannot animate fill-opacity and fill
    together cleanly, so the open state is precomputed as a solid colour."""
    f = [int(fg[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(bg[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(
        f"{round(f[i] * alpha + b[i] * (1 - alpha)):02x}" for i in range(3)
    )


def _schedule(n: int) -> list[float]:
    """Key times: one expand/collapse handover per slot, wrapping seamlessly."""
    tr = min(0.14, 0.32 / n)
    times = [0.0]
    for k in range(n):
        end = (k + 1) / n
        times.append(round(end - tr, 4))
        times.append(round(end, 4))
    times[-1] = 1.0
    return times


def _series(n: int, value_for_phase) -> list:
    """Sample a per-phase value onto the schedule above."""
    out = [value_for_phase(0)]
    for k in range(n):
        out.append(value_for_phase(k))
        out.append(value_for_phase((k + 1) % n))
    return out


def _row_width(slugs: list[str], phase: int) -> float:
    widths = [
        _open_w(s) if i == phase else ICON_CELL for i, s in enumerate(slugs)
    ]
    return sum(widths) + PILL_GAP * (len(slugs) - 1)


def _pill_x(slugs: list[str], index: int, phase: int) -> float:
    x = 0.0
    for j in range(index):
        x += (_open_w(slugs[j]) if j == phase else ICON_CELL) + PILL_GAP
    return x


def _anim(attr: str, values: list, times: list[float],
          ease: str = EASE, ease_fall: str | None = None) -> str:
    if ease_fall is None:
        per_segment = [ease] * (len(times) - 1)
    else:
        per_segment = [
            ease_fall if values[i + 1] < values[i] else ease
            for i in range(len(times) - 1)
        ]
    splines = ";".join(per_segment)
    vals = ";".join(
        f"{v:.2f}" if isinstance(v, float) else str(v) for v in values
    )
    ts = ";".join(f"{t:g}" for t in times)
    return (
        f'<animate attributeName="{attr}" values="{vals}" keyTimes="{ts}" '
        f'keySplines="{splines}" calcMode="spline" dur="{CYCLE}" '
        f'repeatCount="indefinite"/>'
    )


def _pill(slugs: list[str], index: int, colour: str, origin_x: float,
          cy: float) -> str:
    slug = slugs[index]
    n = len(slugs)
    times = _schedule(n)
    label = _label(slug)
    _, path = LOGOS[slug]

    open_fill = _blend(colour, PILL_BASE, 0.16)
    open_w = _open_w(slug)

    xs = _series(n, lambda p: origin_x + _pill_x(slugs, index, p))
    widths = _series(n, lambda p: open_w if p == index else ICON_CELL)
    fills = _series(n, lambda p: open_fill if p == index else PILL_BASE)
    text_op = _series(n, lambda p: 1.0 if p == index else 0.0)
    icon_op = _series(n, lambda p: 1.0 if p == index else 0.68)

    ts = ";".join(f"{t:g}" for t in times)
    splines = ";".join([EASE] * (len(times) - 1))
    x_vals = ";".join(f"{x:.2f},{cy}" for x in xs)

    return (
        f'  <g>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="{x_vals}" keyTimes="{ts}" keySplines="{splines}" '
        f'calcMode="spline" dur="{CYCLE}" repeatCount="indefinite"/>'
        f'<rect x="0" y="{-PILL_H / 2}" width="{ICON_CELL}" height="{PILL_H}" '
        f'rx="12" fill="{PILL_BASE}">'
        f'{_anim("width", widths, times)}'
        f'{_anim("fill", fills, times)}</rect>'
        f'<text x="{ICON_CELL}" y="{FONT * 0.36:.1f}" class="pil" '
        f'fill="{colour}" opacity="0">{escape(label)}'
        f'{_anim("opacity", text_op, times, TEXT_EASE, TEXT_EASE_OUT)}</text>'
        f'<g transform="translate({ICON_CELL / 2},0)">'
        f'<g transform="scale({SCALE:.4f})">'
        f'<g transform="translate(-12,-12)">'
        f'<title>{escape(label)}</title>'
        f'<path d="{path}" fill="{colour}" opacity="0.68">'
        f'{_anim("opacity", icon_op, times)}</path>'
        f'</g></g></g>'
        f'</g>'
    )


def _layout() -> tuple[float, float]:
    """Left edge and content width, centred on the widest row at its widest."""
    widest = max(
        _row_width(slugs, p)
        for _, _, slugs in GROUPS
        for p in range(len(slugs))
    )
    unit = LABEL_W + LABEL_GAP + widest
    return (CANVAS_W - unit) / 2, unit


def render_stack() -> str:
    """Build the stack SVG. Pure: no network, no environment reads."""
    left, unit = _layout()
    label_right = left + LABEL_W
    pill_x0 = label_right + LABEL_GAP
    right = left + unit
    canvas_h = ROW_Y0 + (len(GROUPS) - 1) * ROW_H + PILL_H // 2 + 34

    total = sum(len(s) for _, _, s in GROUPS)
    names = ", ".join(_label(s) for _, _, slugs in GROUPS for s in slugs)

    rows = []
    for r, (group, colour, slugs) in enumerate(GROUPS):
        cy = ROW_Y0 + r * ROW_H
        rows.append(
            f'  <text x="{label_right}" y="{cy + 4}" class="grp" '
            f'text-anchor="end">{escape(group)}</text>'
        )
        rows += [
            _pill(slugs, i, colour, pill_x0, cy)
            for i in range(len(slugs))
        ]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" \
height="{canvas_h}" viewBox="0 0 {CANVAS_W} {canvas_h}" role="img"
     aria-label="Toolchain: {escape(names)}">
  <defs>
    <clipPath id="sback">
      <rect x="0" y="0" width="{CANVAS_W}" height="{canvas_h}" rx="12"/>
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
      .pil {{ font-family: {MONO}; font-size: {FONT}px; font-weight: 500; }}
    </style>
  </defs>
  <rect x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{canvas_h - 1}" rx="12"
        fill="url(#sbackdrop)" stroke="{BORDER}" stroke-opacity="0.3"/>
  <g clip-path="url(#sback)">
    <ellipse cx="70" cy="10" rx="320" ry="170" fill="url(#sauroraA)"/>
    <ellipse cx="{CANVAS_W - 70}" cy="{canvas_h}" rx="330" ry="180"
             fill="url(#sauroraB)"/>
    <rect x="0" y="0" width="{CANVAS_W}" height="{canvas_h}"
          fill="url(#sdots)"/>
  </g>
  <text x="{left}" y="38" class="hdr">~/stack</text>
  <text x="{right}" y="38" class="hdr" text-anchor="end">{total} tools</text>
  <line x1="{left}" y1="50" x2="{right}" y2="50" stroke="{MUTED}"
        stroke-opacity="0.2"/>
{chr(10).join(rows)}
</svg>
"""
