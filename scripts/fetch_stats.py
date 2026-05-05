"""Fetch contribution data from GitHub GraphQL API and compute streak stats."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import requests

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

# GraphQL only allows querying a 1-year window per call. We page in 1-year
# chunks going backwards in time so we can find the *longest-ever* streak,
# not just the longest streak in the last year.
CONTRIB_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    createdAt
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


@dataclass
class Stats:
    total_last_year: int
    current_streak: int
    longest_streak: int
    generated_at: str


def _post(token: str, variables: dict) -> dict:
    headers = {"Authorization": f"bearer {token}"}
    resp = requests.post(
        GITHUB_GRAPHQL_URL,
        json={"query": CONTRIB_QUERY, "variables": variables},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "errors" in payload:
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]["user"]


def _flatten_days(user_data: dict) -> list[tuple[date, int]]:
    weeks = user_data["contributionsCollection"]["contributionCalendar"]["weeks"]
    days: list[tuple[date, int]] = []
    for week in weeks:
        for d in week["contributionDays"]:
            days.append((date.fromisoformat(d["date"]), d["contributionCount"]))
    return days


def fetch_all_history(token: str, login: str) -> tuple[list[tuple[date, int]], int]:
    """Return (all_days_oldest_first, total_in_last_year)."""
    today = datetime.now(timezone.utc)

    last_year_data = _post(
        token,
        {
            "login": login,
            "from": (today - timedelta(days=365)).isoformat(),
            "to": today.isoformat(),
        },
    )
    total_last_year = last_year_data["contributionsCollection"][
        "contributionCalendar"
    ]["totalContributions"]
    created_at = datetime.fromisoformat(
        last_year_data["createdAt"].replace("Z", "+00:00")
    )

    all_days: dict[date, int] = {}
    window_end = today
    while window_end > created_at:
        window_start = max(window_end - timedelta(days=365), created_at)
        data = _post(
            token,
            {
                "login": login,
                "from": window_start.isoformat(),
                "to": window_end.isoformat(),
            },
        )
        for d, count in _flatten_days(data):
            all_days[d] = max(all_days.get(d, 0), count)
        window_end = window_start - timedelta(seconds=1)

    sorted_days = sorted(all_days.items(), key=lambda x: x[0])
    return sorted_days, total_last_year


def compute_streaks(days: list[tuple[date, int]]) -> tuple[int, int]:
    """Return (current_streak, longest_streak) in days."""
    longest = 0
    run = 0
    for _, count in days:
        if count > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    # Current streak: walk backwards from today. If today has no contribution
    # yet, don't break the streak — start from yesterday instead.
    today = date.today()
    current = 0
    by_date = dict(days)
    cursor = today
    if by_date.get(cursor, 0) == 0:
        cursor -= timedelta(days=1)
    while by_date.get(cursor, 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

    return current, longest


def collect(token: str, login: str) -> Stats:
    days, total_last_year = fetch_all_history(token, login)
    current, longest = compute_streaks(days)
    return Stats(
        total_last_year=total_last_year,
        current_streak=current,
        longest_streak=longest,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


if __name__ == "__main__":
    token = os.environ["GH_TOKEN"]
    login = os.environ.get("GH_LOGIN", "Dreyyy25")
    stats = collect(token, login)
    print(stats)
    sys.stdout.flush()
