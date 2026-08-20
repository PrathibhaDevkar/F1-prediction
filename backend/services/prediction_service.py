"""Turns trained models into predictions: a single what-if call
(grid/team/driver/circuit), and a full-grid forecast for the next race.

Returns a predicted position (regression, rounded) plus win/podium/points
probabilities (from separate classifiers) rather than a position-by-
position probability list — closer to what people actually want to know
("will they podium?") than an exact-position guess.
"""
import pandas as pd

from services import fastf1_service
from services.feature_engineering import (
    DEFAULT_AVG_FINISH,
    DEFAULT_DNF_RATE,
    DEFAULT_QUALI_GAP,
    RaceHistory,
)


def build_prediction(
    model_data,
    grid,
    team,
    driver=None,
    circuit=None,
    rolling_features: dict | None = None,
    driver_form: dict | None = None,
    team_form: dict | None = None,
):
    """rolling_features, if given, is used as-is (predict_next_race has a
    live RaceHistory to compute it from). Otherwise driver_form/team_form
    (snapshots saved alongside the model) are looked up by name, falling
    back to league-average defaults — what the manual what-if form uses,
    since it only has the saved snapshot, not a live history.
    """
    row = {"grid": grid, f"team_{team}": 1, "quali_gap": DEFAULT_QUALI_GAP}
    if driver:
        row[f"driver_{driver}"] = 1
    if circuit:
        row[f"circuit_{circuit}"] = 1

    if rolling_features:
        row.update(rolling_features)
    else:
        d_form = (driver_form or {}).get(driver, {})
        t_form = (team_form or {}).get(team, {})
        row["driver_recent_avg_finish"] = d_form.get("driver_recent_avg_finish", DEFAULT_AVG_FINISH)
        row["driver_dnf_rate"] = d_form.get("driver_dnf_rate", DEFAULT_DNF_RATE)
        row["team_recent_avg_finish"] = t_form.get("team_recent_avg_finish", DEFAULT_AVG_FINISH)

    features = model_data["features"]
    input_data = pd.DataFrame([row])
    for col in features:
        if col not in input_data.columns:
            input_data[col] = 0
    input_data = input_data[features]

    position = float(model_data["position_model"].predict(input_data)[0])
    predicted_position = max(1, round(position))

    probabilities = {}
    for name, clf in model_data["classifiers"].items():
        probabilities[f"{name}_probability"] = float(clf.predict_proba(input_data)[0][1])

    return {"predicted_position": predicted_position, **probabilities}


def predict_next_race(
    model_data,
    next_event: dict,
    history: RaceHistory,
    season: int = fastf1_service.CURRENT_SEASON,
):
    """Forecast every current driver's finish for the next race, using the
    live RaceHistory (built during this same training run) for each
    driver/team's exact current rolling form.

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

    circuit = next_event.get("Location", "")

    forecasts = []
    for _, driver in lineup.iterrows():
        abbr = driver["Abbreviation"]
        team = driver["TeamName"]
        grid = grid_by_driver.get(abbr)
        if grid is None or pd.isna(grid):
            continue

        rolling = history.features_before_this_race(abbr, team)
        result = build_prediction(
            model_data, int(grid), team, driver=abbr, circuit=circuit, rolling_features=rolling
        )
        forecasts.append({
            "driver": driver["FullName"],
            "abbreviation": abbr,
            "team": team,
            "assumedGrid": int(grid),
            "assumedGridSource": f"grid from round {last_round}",
            "predictedPosition": result["predicted_position"],
            "podiumProbability": result["podium_probability"],
            "pointsProbability": result["points_probability"],
        })

    forecasts.sort(key=lambda f: f["predictedPosition"])
    return forecasts
