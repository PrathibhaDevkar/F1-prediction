"""Turns trained models into predictions: a single what-if call
(grid/team/driver/circuit), and a full-grid forecast for the next race.

Returns a predicted position (regression, rounded) plus win/podium/points
probabilities (from separate classifiers) rather than a position-by-
position probability list — closer to what people actually want to know
("will they podium?") than an exact-position guess.
"""
import numpy as np
import pandas as pd

from services import fastf1_service
from services.feature_engineering import (
    DEFAULT_AVG_FINISH,
    DEFAULT_DNF_RATE,
    DEFAULT_QUALI_GAP,
    RaceHistory,
)


# Each classifier scores drivers one at a time, so nothing stops a race's
# win probabilities summing to 0.01 or 1.3. But a race has exactly one
# winner, three podium places and ten points places - these are the totals
# a full field's probabilities have to add up to.
RACE_SLOTS = {"win": 1, "podium": 3, "points": 10}


def normalize_to_race(probs, slots: int) -> np.ndarray:
    """Rescale one race's probabilities so they sum to `slots`, by adding
    the same constant to every driver's log-odds. Unlike dividing by the
    sum, this keeps every probability inside [0, 1] (which matters for
    podium/points, where plain scaling can push a favourite past 100%)
    and never changes the order of drivers. Needs more drivers than slots;
    with fewer, returns the input unchanged."""
    p = np.clip(np.asarray(probs, dtype=float), 1e-6, 1 - 1e-6)
    if len(p) <= slots:
        return p
    logits = np.log(p / (1 - p))
    lo, hi = -30.0, 30.0
    for _ in range(60):  # bisection on the shift; total is monotonic in it
        shift = (lo + hi) / 2
        if (1 / (1 + np.exp(-(logits + shift)))).sum() > slots:
            hi = shift
        else:
            lo = shift
    return 1 / (1 + np.exp(-(logits + (lo + hi) / 2)))


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

    Uses the real starting grid once that weekend's qualifying has run;
    until then, falls back to each driver's grid position from their most
    recent race as a stand-in. Which one was used is labelled in the
    response (assumedGridSource), not presented as certain either way.
    """
    lineup = fastf1_service.get_latest_driver_lineup(season)
    if lineup.empty:
        return None

    completed = fastf1_service.get_completed_events(season)
    if not completed:
        return None

    next_round = int(next_event["RoundNumber"])
    real_grid = fastf1_service.get_qualifying_grid(season, next_round)

    if real_grid:
        grid_by_driver = real_grid
        grid_source = "real qualifying result"
    else:
        last_round = int(completed[-1]["RoundNumber"])
        last_session = fastf1_service.get_race_session(season, last_round)
        if last_session is None or last_session.results is None or last_session.results.empty:
            return None
        grid_by_driver = dict(
            zip(last_session.results["Abbreviation"], last_session.results["GridPosition"])
        )
        grid_source = f"grid from round {last_round}"

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
            "assumedGridSource": grid_source,
            "predictedPosition": result["predicted_position"],
            "winProbability": result["win_probability"],
            "podiumProbability": result["podium_probability"],
            "pointsProbability": result["points_probability"],
        })

    for name, slots in RACE_SLOTS.items():
        key = f"{name}Probability"
        normalized = normalize_to_race([f[key] for f in forecasts], slots)
        for f, p in zip(forecasts, normalized):
            f[key] = float(p)

    forecasts.sort(key=lambda f: f["predictedPosition"])
    return forecasts
