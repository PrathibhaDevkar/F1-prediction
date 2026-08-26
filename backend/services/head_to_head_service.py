"""Driver-vs-driver comparison, reading the results snapshot saved
alongside the model (model_trainer.py) instead of hitting FastF1 again —
instant pandas filtering rather than re-fetching ~90 races per request.
"""
import os

import pandas as pd

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_CACHE_PATH = os.path.join(BACKEND_DIR, "race_results.pkl")


def compare_drivers(driver_a: str, driver_b: str) -> dict | None:
    if not os.path.exists(RESULTS_CACHE_PATH):
        return None

    df = pd.read_pickle(RESULTS_CACHE_PATH)
    a = df[df["driver"] == driver_a]
    b = df[df["driver"] == driver_b]
    if a.empty or b.empty:
        return None

    merged = a.merge(b, on=["season", "round"], suffixes=("_a", "_b"))
    if merged.empty:
        return None

    a_wins = int((merged["finish_a"] < merged["finish_b"]).sum())
    b_wins = int((merged["finish_b"] < merged["finish_a"]).sum())

    races = [
        {
            "season": int(row["season"]),
            "round": int(row["round"]),
            "event": row["event_a"],
            "driverAPosition": int(row["finish_a"]) if pd.notna(row["finish_a"]) else None,
            "driverBPosition": int(row["finish_b"]) if pd.notna(row["finish_b"]) else None,
        }
        for _, row in merged.sort_values(["season", "round"]).iterrows()
    ]

    return {
        "driverA": {
            "abbreviation": driver_a,
            "name": a["driver_name"].iloc[-1],
            "wins": a_wins,
            "avgFinish": round(float(merged["finish_a"].mean()), 1),
            "totalPoints": float(merged["points_a"].sum()),
        },
        "driverB": {
            "abbreviation": driver_b,
            "name": b["driver_name"].iloc[-1],
            "wins": b_wins,
            "avgFinish": round(float(merged["finish_b"].mean()), 1),
            "totalPoints": float(merged["points_b"].sum()),
        },
        "racesCompared": len(merged),
        "races": races,
    }
