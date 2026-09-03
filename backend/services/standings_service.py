"""Championship standings, computed from the same results snapshot
head_to_head_service uses — no separate FastF1 call needed since every
session's points are already sitting in race_results.pkl.
"""
import os

import pandas as pd

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_CACHE_PATH = os.path.join(BACKEND_DIR, "race_results.pkl")


def get_standings(season: int) -> dict | None:
    if not os.path.exists(RESULTS_CACHE_PATH):
        return None

    df = pd.read_pickle(RESULTS_CACHE_PATH)
    season_df = df[df["season"] == season]
    if season_df.empty:
        return None

    drivers = (
        season_df.groupby(["driver", "driver_name"])
        .agg(points=("points", "sum"), team=("team", "last"))
        .reset_index()
        .sort_values("points", ascending=False)
    )
    constructors = (
        season_df.groupby("team")
        .agg(points=("points", "sum"))
        .reset_index()
        .sort_values("points", ascending=False)
    )

    return {
        "drivers": [
            {
                "position": i + 1,
                "abbreviation": row["driver"],
                "name": row["driver_name"],
                "team": row["team"],
                "points": float(row["points"]),
            }
            for i, (_, row) in enumerate(drivers.iterrows())
        ],
        "constructors": [
            {
                "position": i + 1,
                "team": row["team"],
                "points": float(row["points"]),
            }
            for i, (_, row) in enumerate(constructors.iterrows())
        ],
    }
