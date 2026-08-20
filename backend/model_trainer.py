"""Trains the finishing-position classifier on real historical F1 results.

Callable directly (train_and_save()) so the Phase 2 retrain pipeline can
invoke it without shelling out, as well as runnable as a script.
"""
import os
import pickle
from datetime import datetime, timezone

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, mean_absolute_error

import db
from services import fastf1_service, model_service, prediction_service
from services.feature_engineering import RaceHistory

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BACKEND_DIR, "model.pkl")

NUMERIC_FEATURES = ["grid", "driver_recent_avg_finish", "team_recent_avg_finish", "driver_dnf_rate"]
CATEGORICAL_FEATURES = ["team", "driver", "circuit"]


def fetch_and_prepare_data() -> tuple[pd.DataFrame, RaceHistory]:
    """Every completed race from EARLIEST_TRAINING_SEASON through the
    current season's most recent completed round, in chronological order,
    with each row's rolling-form features computed from ONLY prior races.

    Returns the DataFrame plus the fully-built RaceHistory (reflecting
    every processed race), which the caller can reuse to compute the same
    features for the next, not-yet-run race.
    """
    dataset = []
    history = RaceHistory()
    current_year = datetime.now(timezone.utc).year

    for season in range(fastf1_service.EARLIEST_TRAINING_SEASON, current_year + 1):
        completed = fastf1_service.get_completed_events(season)
        if not completed:
            continue
        print(f"Season {season}: {len(completed)} completed race(s)")

        for event in completed:
            round_number = int(event["RoundNumber"])
            session = fastf1_service.get_race_session(season, round_number)
            if session is None or session.results is None or session.results.empty:
                print(f"  Skipping {season} round {round_number}: no results")
                continue

            circuit = event.get("Location", "")
            results = session.results

            # Pass 1: compute each driver's rolling features from history
            # BEFORE any of this race's own results are recorded — this is
            # what prevents a race's outcome from leaking into its own
            # features (including via a teammate's result).
            rows = []
            for _, driver in results.iterrows():
                team = driver["TeamName"]
                abbr = driver["Abbreviation"]
                rolling = history.features_before_this_race(abbr, team)
                rows.append({
                    "grid": driver["GridPosition"],
                    "finish": driver["Position"],
                    "team": team,
                    "driver": abbr,
                    "circuit": circuit,
                    "status": driver["Status"],
                    **rolling,
                })
            dataset.extend(rows)

            # Pass 2: now fold this race's actual results into history so
            # they're available for each driver's NEXT race.
            for _, driver in results.iterrows():
                history.record_result(
                    driver["Abbreviation"], driver["TeamName"], driver["Position"], driver["Status"]
                )

    df = pd.DataFrame(dataset)
    if df.empty:
        return df, history

    df["finish"] = pd.to_numeric(df["finish"], errors="coerce")
    df["grid"] = pd.to_numeric(df["grid"], errors="coerce")
    df.dropna(subset=["finish", "grid"], inplace=True)
    df.drop(columns=["status"], inplace=True)
    return df, history


def train_model(df: pd.DataFrame):
    df = pd.get_dummies(df, columns=CATEGORICAL_FEATURES)

    y = df["finish"]
    X = df.drop("finish", axis=1)

    # Chronological split, not random: df is built in race order, so the
    # last ~20% of rows are the most recent races. This mirrors the real
    # task (predict the future from the past) — a random split would let
    # the model "see" rolling-form patterns from races that happened after
    # the ones it's being tested on, which is closer to how it'll actually
    # be used than a random shuffle would be.
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    model = RandomForestClassifier(n_estimators=200, min_samples_leaf=2, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    mae = mean_absolute_error(y_test, preds)
    within_3 = (abs(preds - y_test) <= 3).mean()

    metrics = {"accuracy": accuracy, "mae": mae, "within_3_positions": within_3}
    return model, X.columns.tolist(), metrics


def build_form_snapshots(history: RaceHistory, season: int = fastf1_service.CURRENT_SEASON):
    """Snapshot every current driver/team's rolling form as of the end of
    training, so the manual what-if endpoint (which has no live
    RaceHistory of its own) can still use real current form instead of
    league-average defaults when a driver/team is specified.
    """
    lineup = fastf1_service.get_latest_driver_lineup(season)
    if lineup.empty:
        return {}, {}

    driver_form = {row["Abbreviation"]: history.driver_snapshot(row["Abbreviation"]) for _, row in lineup.iterrows()}
    team_form = {team: history.team_snapshot(team) for team in lineup["TeamName"].unique()}
    return driver_form, team_form


def save_model(model, features, driver_form=None, team_form=None):
    model_data = {
        "model": model,
        "features": features,
        "driver_form": driver_form or {},
        "team_form": team_form or {},
    }
    tmp_path = MODEL_PATH + ".tmp"
    with open(tmp_path, "wb") as f:
        pickle.dump(model_data, f)
    os.replace(tmp_path, MODEL_PATH)
    model_service.reload_model()
    return model_data


def generate_next_race_forecast(model_data, history: RaceHistory):
    """Regenerate the cached next-race forecast; no-ops quietly if there's
    no upcoming race or not enough data to build one."""
    next_event = fastf1_service.get_next_event()
    if next_event is None:
        print("No upcoming race found — skipping next-race forecast.")
        return

    forecast = prediction_service.predict_next_race(model_data, next_event, history=history)
    if forecast is None:
        print("Not enough data to forecast the next race yet.")
        return

    round_key = str(int(next_event["RoundNumber"]))
    db.set_cached_prediction(round_key, forecast, datetime.now(timezone.utc).isoformat())
    print(f"Next-race forecast cached for round {round_key}.")


def train_and_save():
    print("Fetching real historical F1 data (this can take a while on a cold cache)...")
    df, history = fetch_and_prepare_data()
    if df.empty:
        print("Error: No data fetched.")
        return None

    print(f"Dataset compiled with {len(df)} records.")
    model, features, metrics = train_model(df)
    print(
        f"Model accuracy: {metrics['accuracy'] * 100:.2f}% exact | "
        f"within 3 positions: {metrics['within_3_positions'] * 100:.2f}% | "
        f"MAE: {metrics['mae']:.2f} positions"
    )

    driver_form, team_form = build_form_snapshots(history)
    model_data = save_model(model, features, driver_form, team_form)
    print(f"Model and {len(features)} feature references saved to model.pkl")

    generate_next_race_forecast(model_data, history)
    return model_data


if __name__ == "__main__":
    train_and_save()
