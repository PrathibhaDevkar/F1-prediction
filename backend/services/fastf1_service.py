"""Central wrapper around all FastF1 calls: calendar, results, driver lineups.

Every function here returns pandas objects, [], or None on failure — routers
are responsible for turning that into JSON / HTTP error responses.
"""
import os
from datetime import datetime, timezone

import fastf1
import pandas as pd

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BACKEND_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)
fastf1.Cache.enable_cache(CACHE_DIR)

CURRENT_SEASON = 2026
EARLIEST_TRAINING_SEASON = 2023


def get_calendar(season: int = CURRENT_SEASON) -> pd.DataFrame:
    try:
        return fastf1.get_event_schedule(season, include_testing=False)
    except Exception as e:
        print(f"[fastf1_service] Failed to fetch calendar for {season}: {e}")
        return pd.DataFrame()


def race_session_time(event_row) -> datetime | None:
    """Find whichever SessionN is named 'Race' and return its UTC datetime.

    Session5 is 'Race' for every current format (conventional and sprint
    weekends alike), but this checks defensively rather than assuming a
    fixed column, since FastF1's schedule layout has changed across seasons.
    """
    for i in range(5, 0, -1):
        if event_row.get(f"Session{i}") == "Race":
            ts = event_row.get(f"Session{i}DateUtc")
            if pd.notna(ts):
                return ts.to_pydatetime().replace(tzinfo=timezone.utc)
    return None


def get_completed_events(season: int = CURRENT_SEASON) -> list[dict]:
    """Calendar rows (as dicts) whose race session has already happened,
    in round order."""
    calendar = get_calendar(season)
    if calendar.empty:
        return []
    now = datetime.now(timezone.utc)
    completed = []
    for _, row in calendar.iterrows():
        race_time = race_session_time(row)
        if race_time and race_time < now:
            completed.append(row.to_dict())
    return completed


def get_next_event(season: int = CURRENT_SEASON) -> dict | None:
    """The next race whose session hasn't happened yet."""
    calendar = get_calendar(season)
    if calendar.empty:
        return None
    now = datetime.now(timezone.utc)
    upcoming = []
    for _, row in calendar.iterrows():
        race_time = race_session_time(row)
        if race_time and race_time >= now:
            upcoming.append((race_time, row.to_dict()))
    if not upcoming:
        return None
    upcoming.sort(key=lambda pair: pair[0])
    return upcoming[0][1]


def get_race_session(season: int, round_number: int, with_laps: bool = False):
    """Loaded FastF1 Session for a race, or None on failure.

    with_laps=True is needed to read session.total_laps (a real number,
    not a static guess) but costs more to load, so it's opt-in.
    """
    try:
        session = fastf1.get_session(season, round_number, "R")
        session.load(laps=with_laps, telemetry=False, weather=False, messages=False)
        return session
    except Exception as e:
        print(f"[fastf1_service] Failed to load {season} round {round_number}: {e}")
        return None


def get_latest_driver_lineup(season: int = CURRENT_SEASON) -> pd.DataFrame:
    """Driver/team lineup from the most recently completed race of the season."""
    completed = get_completed_events(season)
    if not completed:
        return pd.DataFrame()
    latest_round = int(completed[-1]["RoundNumber"])
    session = get_race_session(season, latest_round)
    if session is None or session.results is None or session.results.empty:
        return pd.DataFrame()
    return session.results[["DriverNumber", "Abbreviation", "FullName", "TeamName"]].copy()
