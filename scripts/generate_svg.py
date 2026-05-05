"""Render the contribution stats into a tokyonight-themed dashboard SVG."""
from __future__ import annotations

import os
from pathlib import Path

from fetch_stats import collect

# tokyonight palette
BG = "#1a1b26"
PANEL = "#24283b"
PRIMARY = "#7aa2f7"
SECONDARY = "#a9b1d6"
ACCENT = "#bb9af7"
GREEN = "#9ece6a"
ORANGE = "#ff9e64"
MUTED = "#565f89"

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="720" height="220" viewBox="0 0 720 220" role="img" aria-labelledby="title">
  <title id="title">GitHub contribution dashboard</title>

  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="{panel}"/>
    </linearGradient>
    <linearGradient id="heroGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{primary}"/>
      <stop offset="100%" stop-color="{accent}"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6"/>
    </filter>
    <style>
      .mono {{ font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace; }}
      .sans {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; }}
      .label {{ fill: {muted}; font-size: 11px; letter-spacing: 1.4px; text-transform: uppercase; }}
      .value {{ fill: {secondary}; font-size: 20px; font-weight: 600; }}
      .hero  {{ fill: url(#heroGrad); font-size: 64px; font-weight: 700; }}
      .sub   {{ fill: {secondary}; font-size: 13px; }}
      .dot   {{ filter: url(#soft); }}
    </style>
  </defs>

  <rect x="0" y="0" width="720" height="220" rx="16" fill="url(#bgGrad)"/>
  <rect x="0" y="0" width="720" height="220" rx="16" fill="none" stroke="{muted}" stroke-opacity="0.35"/>

  <circle class="dot" cx="640" cy="40"  r="22" fill="{accent}"  fill-opacity="0.18"/>
  <circle class="dot" cx="690" cy="190" r="34" fill="{primary}" fill-opacity="0.15"/>

  <g transform="translate(20,18)">
    <circle cx="0"  cy="0" r="5" fill="{orange}"/>
    <circle cx="14" cy="0" r="5" fill="{green}"/>
    <circle cx="28" cy="0" r="5" fill="{primary}"/>
    <text x="48" y="4" class="mono" fill="{muted}" font-size="11">~/ {login} — contribution.dashboard</text>
  </g>

  <line x1="0" y1="42" x2="720" y2="42" stroke="{muted}" stroke-opacity="0.25"/>

  <g transform="translate(36,110)">
    <text class="sans label">contributions · last year</text>
    <text y="56" class="mono hero">{total}</text>
    <text y="86" class="sans sub">commits · PRs · reviews · issues</text>
  </g>

  <g transform="translate(420,72)">
    <rect x="0" y="0" width="270" height="56" rx="10" fill="{panel}" stroke="{muted}" stroke-opacity="0.4"/>
    <circle cx="22" cy="28" r="6" fill="{green}"/>
    <text x="42" y="22" class="sans label">current streak</text>
    <text x="42" y="44" class="mono value">{current} days</text>

    <rect x="0" y="68" width="270" height="56" rx="10" fill="{panel}" stroke="{muted}" stroke-opacity="0.4"/>
    <circle cx="22" cy="96" r="6" fill="{accent}"/>
    <text x="42" y="90" class="sans label">longest streak</text>
    <text x="42" y="112" class="mono value">{longest} days</text>
  </g>

  <text x="700" y="206" text-anchor="end" class="mono" fill="{muted}" font-size="10">updated {ts}</text>
</svg>
"""


def render(out_path: Path) -> None:
    token = os.environ["GH_TOKEN"]
    login = os.environ.get("GH_LOGIN", "Dreyyy25")
    stats = collect(token, login)

    svg = SVG_TEMPLATE.format(
        bg=BG, panel=PANEL, primary=PRIMARY, secondary=SECONDARY,
        accent=ACCENT, green=GREEN, orange=ORANGE, muted=MUTED,
        login=login,
        total=f"{stats.total_last_year:,}",
        current=stats.current_streak,
        longest=stats.longest_streak,
        ts=stats.generated_at,
    )
    out_path.write_text(svg, encoding="utf-8")
    print(f"wrote {out_path} - total={stats.total_last_year} "
          f"current={stats.current_streak} longest={stats.longest_streak}")


if __name__ == "__main__":
    render(Path("custom-stats.svg"))
