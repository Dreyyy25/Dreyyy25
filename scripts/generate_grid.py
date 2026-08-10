"""Render the contribution grid with a crush wave travelling across it.

A wave sweeps left to right; each column squashes flat against the grid's
baseline as the wave passes, overshoots slightly on the way back up, then
settles. Nothing here responds to the cursor, and it can't: GitHub serves
README images through <img>, which hit-tests as a single opaque box, so no
element inside an SVG is ever hoverable. Declarative SMIL animation is the
only motion that survives that boundary.

The squash is one <animateTransform> per column (53 total) rather than one per
square (371), which keeps the file small. Each column group is translated so
its origin sits on the grid's bottom edge; scaling Y about that origin makes
the squares compress downward instead of toward the top.
"""
from __future__ import annotations

from datetime import date, timedelta
from xml.sax.saxutils import escape

# --- Grid geometry ---------------------------------------------------------
CELL = 11
GAP = 3
PITCH = CELL + GAP
WEEKS = 53
DAYS = 7

GRID_W = WEEKS * PITCH - GAP
GRID_H = DAYS * PITCH - GAP

PAD = 18
LABEL_W = 30
GRID_X = PAD + LABEL_W
GRID_Y = 40
GRID_BOTTOM = GRID_Y + GRID_H

CANVAS_W = GRID_X + GRID_W + PAD
CANVAS_H = GRID_BOTTOM + 37

# --- Palette (Tokyo Night) -------------------------------------------------
PANEL = "#1a1b26"
BORDER = "#565f89"
MUTED = "#565f89"
FG = "#c0caf5"
# Neutral ramp: intensity carries the signal, not hue. Runs from just above the
# panel background up to the editor's foreground lavender-white.
LEVELS = ["#1e202c", "#2c3145", "#454d6b", "#7d86ab", "#c0caf5"]

MONO = ("'JetBrains Mono','Fira Code','SFMono-Regular',"
        "Consolas,Menlo,'DejaVu Sans Mono',monospace")

# --- Crush wave ------------------------------------------------------------
CYCLE = "5.2s"
SQUASH = 0.16       # scaleY at full compression
OVERSHOOT = 1.09    # springs past 1 on the way back
STEP = 0.035        # fraction of the cycle each phase of the squash takes
LEAD = 0.02         # wave starts just after the cycle begins
SPAN = 0.78         # fraction of the cycle the wave takes to cross the grid


def _level(count: int, ceiling: int) -> int:
    if count <= 0:
        return 0
    ratio = count / ceiling
    if ratio <= 0.25:
        return 1
    if ratio <= 0.50:
        return 2
    if ratio <= 0.75:
        return 3
    return 4


def _window(today: date) -> date:
    """First Sunday of the 53-week window ending in today's week."""
    days_since_sunday = (today.weekday() + 1) % 7
    return today - timedelta(days=days_since_sunday) - timedelta(weeks=WEEKS - 1)


def _column(col: int, start: date, today: date,
            by_date: dict[date, int], ceiling: int) -> str:
    """One week: seven squares plus the animation that crushes them."""
    x = GRID_X + col * PITCH
    f = LEAD + (col / (WEEKS - 1)) * SPAN

    key_times = f"0;{f:.4f};{f + STEP:.4f};{f + 2 * STEP:.4f};{f + 3 * STEP:.4f};1"
    values = (f"1 1;1 1;1 {SQUASH};1 {OVERSHOOT};1 1;1 1")

    squares = []
    for row in range(DAYS):
        day = start + timedelta(weeks=col, days=row)
        if day > today:
            continue                      # the week in progress
        count = by_date.get(day, 0)
        # y is relative to the column origin, which sits on the grid's bottom
        # edge, so scaling Y compresses the squares downward.
        y = row * PITCH - GRID_H
        squares.append(
            f'<rect x="0" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{LEVELS[_level(count, ceiling)]}">'
            f'<title>{count} on {day.isoformat()}</title></rect>'
        )

    if not squares:
        return ""
    return (
        f'  <g transform="translate({x},{GRID_BOTTOM})"><g>'
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="{values}" keyTimes="{key_times}" dur="{CYCLE}" '
        f'repeatCount="indefinite"/>'
        + "".join(squares) + "</g></g>"
    )


def _month_labels(start: date, today: date) -> str:
    out, last = [], None
    for col in range(WEEKS):
        day = start + timedelta(weeks=col)
        if day > today:
            break
        if day.month != last:
            last = day.month
            # Skip a label that would collide with the right edge.
            if col <= WEEKS - 3:
                out.append(
                    f'  <text x="{GRID_X + col * PITCH}" y="{GRID_Y - 9}" '
                    f'class="lbl">{day.strftime("%b")}</text>'
                )
    return "\n".join(out)


def _day_labels() -> str:
    out = []
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = GRID_Y + row * PITCH + CELL - 2
        out.append(
            f'  <text x="{GRID_X - 8}" y="{y}" class="lbl" '
            f'text-anchor="end">{name}</text>'
        )
    return "\n".join(out)


def _footer(total: int) -> str:
    y = GRID_BOTTOM + 24
    key_x = GRID_X + GRID_W - 108
    swatches = "".join(
        f'<rect x="{key_x + 22 + i * 14}" y="{y - 9}" width="{CELL}" '
        f'height="{CELL}" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(LEVELS)
    )
    label = escape(f"{total:,} contributions in the last year")
    return (
        f'  <text x="{GRID_X}" y="{y}" class="foot">{label}</text>\n'
        f'  <text x="{key_x}" y="{y}" class="lbl" text-anchor="end">Less</text>\n'
        f'  {swatches}\n'
        f'  <text x="{key_x + 22 + 5 * 14 + 4}" y="{y}" class="lbl">More</text>'
    )


def render_grid(days: list[tuple[date, int]], total: int,
                today: date | None = None) -> str:
    """Build the grid SVG. Pure: no network, no environment reads."""
    today = today or date.today()
    start = _window(today)
    by_date = dict(days)

    window_counts = [
        by_date.get(start + timedelta(days=i), 0)
        for i in range((today - start).days + 1)
    ]
    busiest = max(window_counts, default=0)
    ceiling = max(busiest, 4)      # keeps a quiet year from looking saturated

    columns = "\n".join(
        c for c in (
            _column(col, start, today, by_date, ceiling) for col in range(WEEKS)
        ) if c
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" \
height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img"
     aria-label="GitHub contribution grid for the last year, \
{total:,} contributions">
  <defs>
    <style>
      .lbl  {{ font-family: {MONO}; font-size: 10px; fill: {MUTED}; }}
      .foot {{ font-family: {MONO}; font-size: 11px; fill: {FG}; }}
    </style>
  </defs>
  <rect x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{CANVAS_H - 1}" rx="12"
        fill="{PANEL}" stroke="{BORDER}" stroke-opacity="0.3"/>
{_month_labels(start, today)}
{_day_labels()}
{columns}
{_footer(total)}
</svg>
"""
