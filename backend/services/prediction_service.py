"""Turns a trained model + feature list into predictions: a single what-if
call (grid/team/driver/circuit), and a full-grid forecast for the next race.
"""
import pandas as pd

from services import fastf1_service


def build_prediction(model, features, grid, team, driver=None, circuit=None):
    row = {"grid": grid, f"team_{team}": 1}
    if driver:
        row[f"driver_{driver}"] = 1
    if circuit:
        row[f"circuit_{circuit}"] = 1

    input_data = pd.DataFrame([row])
    for col in features:
        if col not in input_data.columns:
            input_data[col] = 0
    input_data = input_data[features]

    prediction = model.predict(input_data)
    proba = model.predict_proba(input_data)[0]
    classes = model.classes_

    prob_list = [
        {"position": int(cls), "probability": float(prob)}
        for cls, prob in zip(classes, proba)
    ]
    prob_list.sort(key=lambda x: x["probability"], reverse=True)

    return {"predicted_position": int(prediction[0]), "probabilities": prob_list[:5]}


def predict_next_race(model_data, next_event: dict, season: int = fastf1_service.CURRENT_SEASON):
    """Forecast every current driver's finish for the next race.

    Real grid positions aren't known until qualifying happens, so this uses
    each driver's grid position from their MOST RECENT race as a stand-in —
    clearly labelled as such in the response, not presented as certain.
    """
    lineup = fastf1_service.get_latest_driver_lineup(season)
    if lineup.empty:
        return None

    completed = fastf1_service.get_completed_events(season)
    if not completed:
        return None

    last_round = int(completed[-1]["RoundNumber"])
    last_session = fastf1_service.get_race_session(season, last_round)
    if last_session is None or last_session.results is None or last_session.results.empty:
        return None

    grid_by_driver = dict(
        zip(last_session.results["Abbreviation"], last_session.results["GridPosition"])
    )

    model = model_data["model"]
    features = model_data["features"]
    circuit = next_event.get("Location", "")

    forecasts = []
    for _, driver in lineup.iterrows():
        abbr = driver["Abbreviation"]
        team = driver["TeamName"]
        grid = grid_by_driver.get(abbr)
        if grid is None or pd.isna(grid):
            continue

        result = build_prediction(model, features, int(grid), team, driver=abbr, circuit=circuit)
        forecasts.append({
            "driver": driver["FullName"],
            "abbreviation": abbr,
            "team": team,
            "assumedGrid": int(grid),
            "assumedGridSource": f"grid from round {last_round}",
            "predictedPosition": result["predicted_position"],
        })

    forecasts.sort(key=lambda f: f["predictedPosition"])
    return forecasts
