from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter, HTTPException

from services import fastf1_service

router = APIRouter(prefix="/api", tags=["schedule"])


@router.get("/calendar")
def get_calendar(season: int = fastf1_service.CURRENT_SEASON):
    calendar = fastf1_service.get_calendar(season)
    if calendar.empty:
        return {"season": season, "races": []}

    now = datetime.now(timezone.utc)
    races = []
    for _, row in calendar.iterrows():
        race_time = fastf1_service.race_session_time(row)
        is_completed = bool(race_time and race_time < now)
        races.append({
            "round": int(row["RoundNumber"]),
            "name": row["EventName"],
            "country": row["Country"],
            "location": row["Location"],
            "date": race_time.isoformat() if race_time else None,
            "status": "completed" if is_completed else "upcoming",
        })

    return {"season": season, "races": races}


@router.get("/races/{season}/{round_number}")
def get_race_detail(season: int, round_number: int):
    session = fastf1_service.get_race_session(season, round_number, with_laps=True)
    if session is None or session.results is None or session.results.empty:
        raise HTTPException(status_code=404, detail="Race results not available yet")

    results = session.results.sort_values("Position")

    podium = []
    for _, driver in results.head(3).iterrows():
        podium.append({
            "position": int(driver["Position"]) if pd.notna(driver["Position"]) else None,
            "driver": driver["FullName"],
            "team": driver["TeamName"],
            "points": float(driver["Points"]) if pd.notna(driver["Points"]) else None,
        })

    full_results = []
    for _, driver in results.iterrows():
        full_results.append({
            "position": int(driver["Position"]) if pd.notna(driver["Position"]) else None,
            "driver": driver["FullName"],
            "team": driver["TeamName"],
            "grid": int(driver["GridPosition"]) if pd.notna(driver["GridPosition"]) else None,
            "points": float(driver["Points"]) if pd.notna(driver["Points"]) else None,
            "status": driver["Status"],
        })

    try:
        laps = int(session.total_laps)
    except Exception:
        laps = None

    return {
        "season": season,
        "round": round_number,
        "eventName": session.event["EventName"],
        "location": session.event["Location"],
        "laps": laps,
        "podium": podium,
        "results": full_results,
    }
