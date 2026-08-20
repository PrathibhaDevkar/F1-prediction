"""Trains the finishing-position classifier on real historical F1 results.

Callable directly (train_and_save()) so the Phase 2 retrain pipeline can
invoke it without shelling out, as well as runnable as a script.
"""
import os
import pickle
from datetime import datetime, timezone

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

import db
from services import fastf1_service, model_service, prediction_service

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BACKEND_DIR, "model.pkl")


def fetch_and_prepare_data() -> pd.DataFrame:
    """Every completed race from EARLIEST_TRAINING_SEASON through the
    current season's most recent completed round."""
    dataset = []
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
            for _, driver in session.results.iterrows():
                dataset.append({
                    "grid": driver["GridPosition"],
                    "finish": driver["Position"],
                    "team": driver["TeamName"],
                    "driver": driver["Abbreviation"],
                    "circuit": circuit,
                })

    df = pd.DataFrame(dataset)
    if df.empty:
        return df

    df["finish"] = pd.to_numeric(df["finish"], errors="coerce")
    df["grid"] = pd.to_numeric(df["grid"], errors="coerce")
    df.dropna(subset=["finish", "grid"], inplace=True)
    return df


def train_model(df: pd.DataFrame):
    df = pd.get_dummies(df, columns=["team", "driver", "circuit"])

    y = df["finish"]
    X = df.drop("finish", axis=1)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)

    return model, X.columns.tolist(), accuracy


def save_model(model, features):
    model_data = {"model": model, "features": features}
    tmp_path = MODEL_PATH + ".tmp"
    with open(tmp_path, "wb") as f:
        pickle.dump(model_data, f)
    os.replace(tmp_path, MODEL_PATH)
    model_service.reload_model()
    return model_data


def generate_next_race_forecast(model_data):
    """Regenerate the cached next-race forecast; no-ops quietly if there's
    no upcoming race or not enough data to build one."""
    next_event = fastf1_service.get_next_event()
    if next_event is None:
        print("No upcoming race found — skipping next-race forecast.")
        return

    forecast = prediction_service.predict_next_race(model_data, next_event)
    if forecast is None:
        print("Not enough data to forecast the next race yet.")
        return

    round_key = str(int(next_event["RoundNumber"]))
    db.set_cached_prediction(round_key, forecast, datetime.now(timezone.utc).isoformat())
    print(f"Next-race forecast cached for round {round_key}.")


def train_and_save():
    print("Fetching real historical F1 data (this can take a while on a cold cache)...")
    df = fetch_and_prepare_data()
    if df.empty:
        print("Error: No data fetched.")
        return None

    print(f"Dataset compiled with {len(df)} records.")
    model, features, accuracy = train_model(df)
    print(f"Model accuracy: {accuracy * 100:.2f}%")

    model_data = save_model(model, features)
    print(f"Model and {len(features)} feature references saved to model.pkl")

    generate_next_race_forecast(model_data)
    return model_data


if __name__ == "__main__":
    train_and_save()
